import sys,json,traceback,hashlib,shutil,datetime
from pathlib import Path
import unreal
ROOT=Path('D:/FallLine');sys.path.insert(0,str(ROOT/'Scripts'))
report=dict(passed=False,saved=False)
try:
 b=ROOT/'Saved/Backups'/('SimpleCombined-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));b.mkdir(parents=True)
 files=[]
 for prefix in ['Content','Scripts','Source','SourceAssets']:
  for f in (ROOT/prefix).rglob('*'):
   if f.is_file():
    rel=f.relative_to(ROOT);dst=b/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dst)
    h=hashlib.sha256(f.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==h,str(rel)
    files.append(dict(path=str(rel),sha256=h))
 receipt=b/'verified-backup.json';receipt.write_text(json.dumps(dict(verified=True,files=files),indent=2))
 report['backup_receipt']=str(receipt)
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert level.load_level('/Game/Maps/TestSlope')
 import CreateSnowMaterial,ApplyLandscapeSurfaceDetail,ApplySimpleNoiseForest
 CreateSnowMaterial.create_snow()
 report['terrain']=ApplyLandscapeSurfaceDetail.apply()
 report['forest']=ApplySimpleNoiseForest.apply(verified_backup_receipt=str(receipt),snow_ready=True)
 assert report['terrain']['passed'] and report['forest']['passed']
 assert level.save_current_level()
 report.update(passed=True,saved=True)
except Exception:
 report['error']=traceback.format_exc();unreal.log_error(report['error'])
finally:
 (ROOT/'Saved/Logs/simple-combined-apply.json').write_text(json.dumps(report,indent=2))
