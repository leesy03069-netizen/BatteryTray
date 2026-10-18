"""Lightweight dual HID battery tray; only fixed battery-status queries are sent."""
import ctypes
import json
import os
import pathlib
import sys
import threading
import time
from functools import lru_cache

import pystray
from PIL import Image, ImageDraw, ImageFont
from pystray._util import win32

from profiles import default_config, load_config, query_device, save_config, validate_config
from settings_ui import Settings
from ui_v2 import AlertPolicy, Details, freshness

APP_DIR=pathlib.Path(os.environ.get('LOCALAPPDATA',pathlib.Path.home()))/'BatteryTray'
APP_DIR.mkdir(parents=True,exist_ok=True)
CONFIG_PATH=APP_DIR/'devices.json'
BASE=pathlib.Path(sys.executable).parent if getattr(sys,'frozen',False) else pathlib.Path(__file__).parent
STOP=threading.Event();LOCK=threading.RLock();ICONS=[];STATE=[None,None];ALERTS=[AlertPolicy(),AlertPolicy()]
CONFIG=load_config(CONFIG_PATH) if CONFIG_PATH.exists() else default_config()
DETAILS=None;SETTINGS=None

class BatteryIcon(pystray.Icon):
    def _message(self,code,flags,**kwargs):
        return win32.Shell_NotifyIcon(code,win32.NOTIFYICONDATAW(cbSize=ctypes.sizeof(win32.NOTIFYICONDATAW),hWnd=self._hwnd,hID=1 if self.name=='BatteryTray0' else 2,uFlags=flags,**kwargs))

def cfg_snapshot():
    with LOCK:return json.loads(json.dumps(CONFIG))

def apply_config(c):
    global CONFIG
    c=validate_config(c);save_config(CONFIG_PATH,c)
    with LOCK:
        CONFIG=c;STATE[:]=[None,None]
        if DETAILS:DETAILS.names[:]=[d['name'] for d in c['devices']]
    for a in ALERTS:a.sent.clear()
    for i,icon in enumerate(ICONS):icon.title=c['devices'][i]['name']+'：等待设备响应'

def refresh_settings(icon=None,item=None):
    if DETAILS:DETAILS.commands.put('settings')

def read_one(d):
    try:return query_device(d)
    except Exception:return None

@lru_cache(maxsize=8)
def font(size,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)

def image(percent,index,charging=False,inactive=False):
    im=Image.new('RGBA',(64,64));g=ImageDraw.Draw(im);color='#30d158' if index==0 else '#64d2ff'
    if percent is not None and percent<=20:color='#ff453a'
    elif percent is not None and percent<=50:color='#ffd60a'
    if inactive:color='#929298'
    g.rounded_rectangle((1,1,62,62),radius=15,fill='#202125');g.arc((3,3,60,60),-90,270,fill='#414247',width=3)
    if percent is not None and percent>0:g.arc((3,3,60,60),-90,-90+3.6*percent,fill=color,width=3)
    text='--' if percent is None else str(percent)
    g.text((32,29),text,font=font(36 if len(text)<3 else 29,True),anchor='mm',fill=color)
    g.text((26 if charging else 32,48),'M' if index==0 else 'K',font=font(11),anchor='mm',fill='#e4e4e8')
    if charging and not inactive:g.polygon([(41,40),(36,48),(40,48),(37,56),(46,45),(42,45),(45,40)],fill='#ffd60a')
    return im

def quit_app(icon=None,item=None):
    STOP.set()
    for x in ICONS:x.stop()
    if DETAILS:DETAILS.commands.put('quit')

def toggle_details(icon=None,item=None):
    if DETAILS:DETAILS.commands.put('toggle')

def worker():
    while not STOP.is_set() and not all(x.visible for x in ICONS):STOP.wait(.05)
    drawn=[None,None];last_draw=[0,0]
    while not STOP.is_set():
        c=cfg_snapshot()
        for index,icon in enumerate(ICONS):
            value=read_one(c['devices'][index])
            with LOCK:
                if c!=CONFIG:break
                if value:STATE[index]=value
                s=STATE[index]
            state=freshness(s);d=c['devices'][index]
            label='等待设备响应' if s is None else str(s['percent'])+'%'+(' · 充电中' if s['charging'] and state=='live' else '')+(' · 暂未响应，保留上次读数' if state=='stale' else ' · 离线/休眠，上次读数' if state=='offline' else '')
            icon.title=d['name']+'：'+label
            sig=(None if s is None else s['percent'],index,bool(s and s['charging'] and state=='live'),state!='live')
            if sig!=drawn[index] or time.time()-last_draw[index]>15:
                icon.icon=image(*sig);drawn[index]=sig;last_draw[index]=time.time()
            threshold=ALERTS[index].update(value,value is not None)
            if threshold is not None:icon.notify(d['name']+'剩余 '+str(value['percent'])+'%，记得充电。','外设低电量提醒')
        (APP_DIR/'status.json').write_text(json.dumps({'updated':time.time(),'devices':STATE},ensure_ascii=False,indent=2),encoding='utf-8')
        STOP.wait(c['poll_seconds'])

def main():
    global DETAILS,SETTINGS
    ctypes.windll.kernel32.CreateMutexW.restype=ctypes.c_void_p
    ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\BatteryTrayPublic')
    if ctypes.windll.kernel32.GetLastError()==183:return
    DETAILS=Details(STATE,[d['name'] for d in CONFIG['devices']],STOP,quit_app)
    SETTINGS=Settings(DETAILS.root,cfg_snapshot,apply_config)
    DETAILS.settings=SETTINGS
    if '--settings' in sys.argv:DETAILS.root.after(500,SETTINGS.show)
    if '--show' in sys.argv:DETAILS.root.after(500,DETAILS.show)
    # Read once before icon registration to avoid displaying a stale startup placeholder.
    for i,d in enumerate(CONFIG['devices']):STATE[i]=read_one(d)
    for i,d in enumerate(CONFIG['devices']):
        s=STATE[i];title=d['name']+('：'+str(s['percent'])+'%' if s else '：等待设备响应')
        menu=pystray.Menu(pystray.MenuItem('查看电量详情',toggle_details,default=True),pystray.MenuItem('设备设置…',refresh_settings),pystray.MenuItem('退出',quit_app))
        ICONS.append(BatteryIcon('BatteryTray'+str(i),image(None if s is None else s['percent'],i,bool(s and s['charging'])),title,menu=menu))
    for i in ICONS:i.run_detached()
    threading.Thread(target=worker,daemon=True).start();DETAILS.run()

if __name__=='__main__':main()
