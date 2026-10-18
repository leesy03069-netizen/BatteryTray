"""Strict configuration and two fixed, documented battery query protocols."""
import copy
import json
import pathlib
import re
import time
import hid

PROTOCOLS={'compx_mouse':'ATK / Compx 鼠标（Report 08）','beiying_keyboard':'Beiying 键盘（Report 13）'}
DEFAULT={'schema':1,'poll_seconds':3,'devices':[
 {'role':'mouse','name':'ATK A9 Plus 鼠标','vid':'373B','pid':'10C9','usage_page':'FF02','protocol':'compx_mouse'},
 {'role':'keyboard','name':'键盘 · F87 Pro（用户标注）','vid':'3554','pid':'FA09','usage_page':'FF02','protocol':'beiying_keyboard'}]}

def default_config():return copy.deepcopy(DEFAULT)

def validate_config(config):
    c=copy.deepcopy(config)
    if type(c) is not dict or c.get('schema')!=1:raise ValueError('配置 schema 必须为 1')
    if type(c.get('poll_seconds')) is not int or not 2<=c['poll_seconds']<=60:raise ValueError('刷新间隔须为 2–60 秒的整数')
    if type(c.get('devices')) is not list or len(c['devices'])!=2:raise ValueError('需要鼠标、键盘两个配置槽位')
    for index,d in enumerate(c['devices']):
        role=['mouse','keyboard'][index]
        if type(d) is not dict or d.get('role')!=role:raise ValueError('配置顺序必须为鼠标、键盘')
        if not isinstance(d.get('name'),str) or not 1<=len(d['name'])<=32:raise ValueError('设备名称须为 1–32 个字符')
        for key in ['vid','pid','usage_page']:
            if not isinstance(d.get(key),str) or not re.fullmatch('[0-9A-Fa-f]{4}',d[key]):raise ValueError(key+' 必须为四位十六进制，不含 0x 或空格')
        if d.get('protocol')!=['compx_mouse','beiying_keyboard'][index]:raise ValueError('此槽位只接受对应的内置已知协议')
    return c

def load_config(path):
    path=pathlib.Path(path)
    return validate_config(json.loads(path.read_text(encoding='utf-8'))) if path.exists() else default_config()

def save_config(path,config):
    c=validate_config(config);p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix('.tmp');temp.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(p)

def packet_for(protocol):
    if protocol=='compx_mouse':
        p=[8,4]+[0]*14;p.append((85-sum(p))&255)
    elif protocol=='beiying_keyboard':
        p=[19,74,1]+[0]*16;p.append(sum(p)&255)
    else:raise ValueError('不支持的协议')
    return p

def parse_reply(protocol,r):
    if protocol=='compx_mouse' and len(r)==17 and r[:2]==[8,4] and (sum(r)&255)==85 and 0<=r[6]<=100:
        return {'percent':r[6],'charging':bool(r[7])}
    if protocol=='beiying_keyboard' and len(r)==20 and r[:3]==[19,74,1] and (sum(r[:-1])&255)==r[-1] and 0<=r[5]<=100:
        return {'percent':r[5],'charging':((r[6]>>4)&15)==1}
    return None

def enumerate_receivers():
    result=[]
    for d in hid.enumerate():
        if d['usage_page']<0xff00:continue
        result.append({'vid':f"{d['vendor_id']:04X}",'pid':f"{d['product_id']:04X}",'usage_page':f"{d['usage_page']:04X}",'usage':f"{d['usage']:04X}",'product':d.get('product_string') or '未命名接收器','path':d['path']})
    return result

def query_device(profile):
    endpoints=[d for d in hid.enumerate(int(profile['vid'],16),int(profile['pid'],16)) if d['usage_page']==int(profile['usage_page'],16)]
    if profile['protocol']=='compx_mouse':endpoints.sort(key=lambda d:b'col05' not in d['path'].lower())
    for d in endpoints:
        h=hid.device()
        try:
            h.open_path(d['path'])
            # Battery status requests only; no arbitrary command input.
            if h.write(packet_for(profile['protocol']))<=0:continue
            r=h.read(64,450);value=parse_reply(profile['protocol'],r)
            if value:return dict(value,raw=r,time=time.time())
        except (OSError,ValueError):pass
        finally:h.close()
    return None
