import sys,json,traceback,hashlib
from pathlib import Path
import unreal
ROOT=Path("D:/FallLine");sys.path.insert(0,str(ROOT/"Scripts"))
report=dict(saved=False,passed=False,scope="325 listed mature pairs then136 juvenile trunks ONLY; no material changes")
try:
    ab=json.loads((ROOT/"Saved/Screenshots/ActualPlayer/player-camera-ab-inspection-1794231157530711700.json").read_text())
    assert ab["valid_same_pose_camera_comparison"] and ab["process_exit"]==0
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert level.load_level("/Game/Maps/TestSlope")
    import ApplyForestEdgeStructural,ReconcileJuvenileTrunks
    report["mature"]=ApplyForestEdgeStructural.apply(camera_ab_complete=True)
    assert report["mature"]["passed"]
    report["juvenile"]=ReconcileJuvenileTrunks.apply()
    assert report["juvenile"]["passed"]
    assert hashlib.sha256((ROOT/"Scripts/CreateSnowMaterial.py").read_bytes()).hexdigest()=="155f6631c10ad2257d110fdeed365c05d88682d3b5329f4fc7d475c87f547475"
    assert level.save_current_level()
    report.update(saved=True,passed=True)
except Exception:
    report["error"]=traceback.format_exc()
    unreal.log_error(report["error"])
finally:
    (ROOT/"Saved/Logs/forest-approved-apply-result.json").write_text(json.dumps(report,indent=2))
