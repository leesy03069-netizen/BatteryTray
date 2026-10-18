"""Reproducible Windows directory build; no local logs/config in releases."""
import pathlib,subprocess,sys,shutil,zipfile,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=ROOT,check=True)
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir','--exclude-module','numpy','--exclude-module','charset_normalizer','--name','BatteryTray','--hidden-import','pystray._win32','app.py'],cwd=ROOT,check=True)
out=ROOT/'dist/BatteryTray'
for name in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md','devices.example.json']:shutil.copy2(ROOT/name,out/name)
shutil.copytree(ROOT/'licenses',out/'licenses',dirs_exist_ok=True)
sources=out/'source';sources.mkdir(exist_ok=True)
for name in ['app.py','ui_v2.py','settings_ui.py','profiles.py','requirements.txt','build_release.py']:shutil.copy2(ROOT/name,sources/name)
shutil.copytree(ROOT/'tests',sources/'tests',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
archive=ROOT/'dist/BatteryTray-Windows-x64.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in out.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(out.parent))
print('Artifact:',archive,'SHA256:',hashlib.sha256(archive.read_bytes()).hexdigest())
