import sys,json,traceback,hashlib
from pathlib import Path
import unreal
ROOT=Path("D:/FallLine");sys.path.insert(0,str(ROOT/"Scripts"))
out=ROOT/"Saved/Logs/organic-owner-apply.json"
report=dict(passed=False,saved=False)
try:
 level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 assert level.load_level("/Game/Maps/TestSlope")
 import ApplyForestOrganicTaper as helper
 assert hashlib.sha256((ROOT/"Scripts/ApplyForestOrganicTaper.py").read_bytes()).hexdigest()=="afbca958c8bbb747953622fae60a7828dd17b1930fb2f0e7db2c2d5b3f016ca6"
 report["preflight"]=helper.preflight_only(snow_restored_and_previous_editor_exited=True)
 assert report["preflight"]["passed"]
 report["apply"]=helper.apply(snow_restored_and_previous_editor_exited=True)
 assert report["apply"]["passed"] and report["apply"]["save_authorized_after_all_checks"]
 assert level.save_current_level()
 report.update(passed=True,saved=True)
except Exception:
 report["error"]=traceback.format_exc();unreal.log_error(report["error"])
finally:
 out.write_text(json.dumps(report,indent=2))
