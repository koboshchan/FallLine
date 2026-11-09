import sys,json,traceback,hashlib
from pathlib import Path
import unreal
ROOT=Path("D:/FallLine");sys.path.insert(0,str(ROOT/"Scripts"))
files=["Scripts/CreateSnowMaterial.py","Content/Environment/Snow/M_AlpineSnow.uasset","Content/Maps/TestSlope.umap"]
before={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
report=dict(scope="inventory_readonly ONLY",before=before)
try:
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSlope")
    import SnowDiagnostics
    result=SnowDiagnostics.inventory_readonly()
    report["query_completed"]=True
except Exception:
    report["error"]=traceback.format_exc()
finally:
    report["after"]={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    report["unchanged"]=report["before"]==report["after"]
    (ROOT/"Saved/Logs/snow-inventory-result.json").write_text(json.dumps(report,indent=2))
