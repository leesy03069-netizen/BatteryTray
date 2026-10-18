"""Battery details UI and alert policy. No device commands in this module."""
import time
import queue
import ctypes
import tkinter as tk

class AlertPolicy:
    def __init__(self):
        self.sent = set()
    def update(self, reading, fresh=True):
        if not reading or not fresh:
            return None
        p = reading['percent']
        if reading['charging']:
            return None
        if p > 25:
            self.sent.clear()
        threshold = 10 if p <= 10 else 20 if p <= 20 else None
        if threshold is None or threshold in self.sent:
            return None
        self.sent.add(threshold)
        if threshold == 10:
            self.sent.add(20)
        return threshold

def freshness(reading, now=None):
    if reading is None:
        return 'unknown'
    age = (time.time() if now is None else now) - reading['time']
    return 'offline' if age > 60 else 'stale' if age > 15 else 'live'

class Details:
    def __init__(self, states, names, stop, on_quit):
        self.states, self.names, self.stop = states, names, stop
        self.commands = queue.Queue()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title('外设电量 · 详情')
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#010203')
        self.root.wm_attributes('-transparentcolor', '#010203')
        self.c = tk.Canvas(self.root, width=360, height=310, bg='#010203', highlightthickness=0)
        self.c.pack()
        self.c.bind('<Button-1>', self.click)
        self.root.bind('<Escape>', lambda e:self.root.withdraw())
        self.root.bind('<FocusOut>', self.focus_out)
        self.on_quit = on_quit
        self.visible = False
        self.root.after(100,self.tick)
    def focus_out(self,event):
        self.root.after(150,self.hide_if_unfocused)
    def hide_if_unfocused(self):
        if self.root.focus_displayof() is None:
            self.root.withdraw()
            self.visible=False
    def click(self,e):
        if e.y<54 and e.x>310:
            self.root.withdraw(); self.visible=False
    def rounded(self,x1,y1,x2,y2,r,fill):
        c=self.c
        c.create_rectangle(x1+r,y1,x2-r,y2,fill=fill,outline='')
        c.create_rectangle(x1,y1+r,x2,y2-r,fill=fill,outline='')
        for x,y in [(x1,y1),(x2-2*r,y1),(x1,y2-2*r),(x2-2*r,y2-2*r)]:
            c.create_oval(x,y,x+2*r,y+2*r,fill=fill,outline='')
    def draw(self):
        c=self.c;c.delete('all')
        self.rounded(2,2,358,308,22,'#f5f5f7')
        c.create_text(24,29,text='外设电量',anchor='w',fill='#1d1d1f',font=('Microsoft YaHei UI',15,'bold'))
        c.create_text(331,29,text='×',fill='#86868b',font=('Segoe UI',19))
        for i,s in enumerate(list(self.states)):
            y=60+i*98
            f=freshness(s)
            col=('#30b65b' if i==0 else '#2196ed') if f=='live' else '#a1a1aa'
            if s and f=='live' and s['percent']<=20:col='#ff453a'
            self.rounded(16,y,344,y+88,15,'#ffffff')
            c.create_oval(31,y+16,87,y+72,outline='#ececf0',width=4)
            if s:
                c.create_arc(31,y+16,87,y+72,start=90,extent=-min(359.9,max(.01,3.6*s['percent'])),outline=col,width=4,style='arc')
            c.create_text(59,y+44,text='M' if i==0 else 'K',font=('Segoe UI',16,'bold'),fill=col)
            c.create_text(102,y+27,text=self.names[i],anchor='w',font=('Microsoft YaHei UI',10,'bold'),fill='#1d1d1f')
            txt='等待设备响应' if not s else '充电中 ⚡' if s['charging'] and f=='live' else '已连接' if f=='live' else '暂未响应 · 上次读数' if f=='stale' else '离线 / 休眠 · 上次读数'
            c.create_text(102,y+55,text=txt,anchor='w',font=('Microsoft YaHei UI',9),fill='#86868b')
            c.create_text(325,y+29,text='--' if not s else str(s['percent'])+'%',anchor='e',font=('Segoe UI',19,'bold'),fill=col)
        c.create_text(24,274,text='每 3 秒查询 · 电量为设备估算值',anchor='w',font=('Microsoft YaHei UI',9),fill='#86868b')
        c.create_text(24,293,text='低于 20% / 10% 时各提醒一次',anchor='w',font=('Microsoft YaHei UI',8),fill='#a1a1aa')
    def show(self):
        from ctypes import wintypes
        pt=wintypes.POINT();ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        class RECT(ctypes.Structure):
            _fields_=[('left',ctypes.c_long),('top',ctypes.c_long),('right',ctypes.c_long),('bottom',ctypes.c_long)]
        class INFO(ctypes.Structure):
            _fields_=[('size',ctypes.c_ulong),('monitor',RECT),('work',RECT),('flags',ctypes.c_ulong)]
        u=ctypes.windll.user32;u.MonitorFromPoint.argtypes=[wintypes.POINT,ctypes.c_ulong];u.MonitorFromPoint.restype=wintypes.HANDLE
        monitor=u.MonitorFromPoint(pt,2);info=INFO();info.size=ctypes.sizeof(info)
        u.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.POINTER(INFO)];u.GetMonitorInfoW(monitor,ctypes.byref(info))
        x=max(info.work.left,min(pt.x-180,info.work.right-370))
        y=max(info.work.top,min(pt.y-325,info.work.bottom-320))
        self.root.geometry('360x310+%d+%d'%(x,y));self.draw();self.root.deiconify();self.root.lift();self.root.focus_force();self.visible=True
    def tick(self):
        if self.stop.is_set():
            self.root.destroy();return
        try:
            while True:
                command=self.commands.get_nowait()
                if command=='toggle':
                    if self.visible:self.root.withdraw();self.visible=False
                    else:self.show()
                elif command=='show':self.show()
                elif command=='settings':self.settings.show()
                elif command=='quit':self.stop.set()
        except queue.Empty:pass
        if self.visible:self.draw()
        self.root.after(250,self.tick)
    def run(self):self.root.mainloop()
