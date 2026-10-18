"""Chinese receiver picker; scan only enumerates, never sends probe commands."""
import copy
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from profiles import PROTOCOLS, enumerate_receivers, validate_config

class Settings:
    def __init__(self,root,get_config,on_save):
        self.root=root;self.get_config=get_config;self.on_save=on_save;self.window=None;self.rows=[];self.fields=[]
    def show(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.lift();return
        w=self.window=tk.Toplevel(self.root);w.title('外设电量 · 设备设置');w.geometry('640x580');w.resizable(False,False)
        outer=ttk.Frame(w,padding=20);outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='选择接收器，使用已知协议',font=('Microsoft YaHei UI',14,'bold')).pack(anchor='w')
        ttk.Label(outer,text='仅同协议设备可通过改配置接入；扫描到设备不代表兼容。\n协议不明确时请勿试选，先查官方驱动或提交兼容性申请。',wraplength=590).pack(anchor='w',pady=(8,14))
        self.fields=[];config=self.get_config()
        for i,d in enumerate(config['devices']):
            box=ttk.LabelFrame(outer,text='鼠标' if i==0 else '键盘',padding=10);box.pack(fill='x',pady=5)
            v={k:tk.StringVar(value=d[k]) for k in ['name','vid','pid','usage_page','protocol']};self.fields.append(v)
            ttk.Label(box,text='名称').grid(row=0,column=0,sticky='w');ttk.Entry(box,textvariable=v['name'],width=40).grid(row=0,column=1,columnspan=3,sticky='w')
            for j,k in enumerate(['vid','pid','usage_page']):
                ttk.Label(box,text={'vid':'VID','pid':'PID','usage_page':'Usage Page'}[k]).grid(row=1,column=j*2,sticky='w',pady=8)
                ttk.Entry(box,textvariable=v[k],width=7).grid(row=1,column=j*2+1,sticky='w',padx=4)
            ttk.Label(box,text='协议：'+PROTOCOLS[d['protocol']]).grid(row=2,column=0,columnspan=6,sticky='w')
            pick=ttk.Combobox(box,state='readonly',width=69);pick.grid(row=3,column=0,columnspan=6,sticky='w',pady=(8,0));v['picker']=pick
            pick.bind('<<ComboboxSelected>>',lambda e,n=i:self.choose(n))
        bottom=ttk.Frame(outer);bottom.pack(fill='x',pady=10)
        ttk.Label(bottom,text='刷新间隔（2–60 秒）').pack(side='left');self.interval=tk.StringVar(value=str(config['poll_seconds']))
        ttk.Spinbox(bottom,from_=2,to=60,textvariable=self.interval,width=5).pack(side='left',padx=8)
        ttk.Button(bottom,text='扫描接收器',command=self.scan).pack(side='right')
        self.status=tk.StringVar(value='填写四位十六进制，例如 373B；不带 0x。')
        ttk.Label(outer,textvariable=self.status,wraplength=585).pack(anchor='w',pady=5)
        ttk.Button(outer,text='保存并立即应用',command=self.save).pack(side='right',pady=6)
        self.scan()
    def scan(self):
        self.status.set('正在枚举 HID 接收器（不发送查询命令）…')
        def task():
            try:result=enumerate_receivers();error=None
            except Exception as e:result=[];error=str(e)
            # Tk callbacks are dispatched on the main thread through polling.
            self.pending=(result,error)
        self.pending=None;threading.Thread(target=task,daemon=True).start();self.window.after(100,self.finish_scan)
    def finish_scan(self):
        if not self.window.winfo_exists():return
        if self.pending is None:self.window.after(100,self.finish_scan);return
        self.rows,error=self.pending
        labels=[f"{r['product'][:28]} | {r['vid']}:{r['pid']} | UP {r['usage_page']} | {i+1}" for i,r in enumerate(self.rows)]
        for v in self.fields:v['picker']['values']=labels
        self.status.set('扫描失败：'+error if error else f'找到 {len(self.rows)} 个厂商接口。选择后自动填写 VID / PID / Usage Page。')
    def choose(self,index):
        n=self.fields[index]['picker'].current()
        if n<0:return
        r=self.rows[n]
        for k in ['vid','pid','usage_page']:self.fields[index][k].set(r[k])
    def save(self):
        try:
            c=copy.deepcopy(self.get_config());c['poll_seconds']=int(self.interval.get())
            for i,v in enumerate(self.fields):
                for k in ['name','vid','pid','usage_page','protocol']:c['devices'][i][k]=v[k].get()
            c=validate_config(c)
            old=self.get_config()
            changed=any(any(a[k]!=b[k] for k in ['vid','pid','usage_page','protocol']) for a,b in zip(old['devices'],c['devices']))
            if changed and not messagebox.askyesno('确认已知协议', '改 VID/PID 仅适用于已确认使用相同协议的设备。\n你是否已核实它使用所选内置协议？',parent=self.window):return
            self.on_save(c);self.status.set('已保存，下一轮查询生效。')
        except (ValueError,OSError) as e:messagebox.showerror('配置未保存',str(e),parent=self.window)
