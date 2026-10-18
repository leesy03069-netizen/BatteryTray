import pathlib,tempfile,threading,time,tkinter as tk
from profiles import default_config,save_config,load_config
from settings_ui import Settings
root=tk.Tk();root.withdraw();saved=[]
with tempfile.TemporaryDirectory() as tmp:
    path=pathlib.Path(tmp)/'devices.json'
    def save(c):save_config(path,c);saved.append(load_config(path))
    settings=Settings(root,default_config,save);settings.show()
    end=time.monotonic()+5
    while time.monotonic()<end:
        root.update()
        if settings.pending is not None and settings.rows:break
        time.sleep(.05)
    assert len(settings.rows)>0,'enumeration UI did not populate'
    mouse=next(i for i,r in enumerate(settings.rows) if r['vid']=='373B' and r['pid']=='10C9' and r['usage_page']=='FF02')
    keyboard=next(i for i,r in enumerate(settings.rows) if r['vid']=='3554' and r['pid']=='FA09' and r['usage_page']=='FF02')
    for slot,n in enumerate([mouse,keyboard]):
        settings.fields[slot]['picker'].current(n);settings.choose(slot)
    settings.interval.set('5');settings.save();root.update()
    for child in settings.window.winfo_children():
        def check(widget):
            if widget.winfo_manager():
                bottom=widget.winfo_rooty()+widget.winfo_height()
                assert bottom<=settings.window.winfo_rooty()+settings.window.winfo_height(),('clipped',widget.winfo_class(),bottom)
            for item in widget.winfo_children():check(item)
        check(child)
    assert saved and saved[0]['poll_seconds']==5
    assert saved[0]['devices']==default_config()['devices']
    print('GUI receiver scan, selection, save and config readback: PASS')
    print('enumerated interfaces:',len(settings.rows))
root.destroy()
