import sys,json,traceback
from pathlib import Path
import unreal
ROOT=Path("D:/FallLine");sys.path.insert(0,str(ROOT/"Scripts"))
report=dict(scope="READONLY preflight_only; no apply/save/material/136 changes",passed=False)
try:
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSlope")
    import ApplyForestEdgeStructural
    report["result"]=ApplyForestEdgeStructural.preflight_only()
    report["passed"]=True
except Exception:
    report["error"]=traceback.format_exc()
    unreal.log_error(report["error"])
finally:
    (ROOT/"Saved/Logs/forest-readonly-preflight-result.json").write_text(json.dumps(report,indent=2))
