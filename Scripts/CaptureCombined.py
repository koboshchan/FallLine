"""Single editor refresh + actual PIE player + editor environment detail captures."""
import sys,runpy,json,hashlib,shutil,time,math
from pathlib import Path
ROOT=Path("D:/FallLine")
sys.path.insert(0,str(ROOT/"Scripts"))
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
try:
    gate=json.loads((ROOT/"Saved/Logs/fir-uv-finish-result.json").read_text())
    assert gate["passed"]
    base=ROOT/"SourceAssets/PolyHaven/fir_tree_01"
    rec=json.loads((base/"single-fir-manifest.json").read_text())
    assert rec["sha256"]=="8f159cf815375cc1ce4361ab08fb5f63774b4103cabb8d1847819518aa915829"
    assert hashlib.file_digest((base/rec["output"]).open("rb"),"sha256").hexdigest()==rec["sha256"]
    from ValidateAlpineDependencies import validate_alpine_dependencies
    validate_alpine_dependencies()
    backup=ROOT/"Saved/Backups"/("Combined-"+str(time.time_ns()))
    backup.mkdir(parents=True)
    for rel in ["Content/Maps/TestSlope.umap","Content/Environment/PolyHaven/fir_tree_01/SM_MatureFirA.uasset"]:
        f=ROOT/rel
        if f.exists(): shutil.copy2(f,backup/f.name)
    # Parent forest worker must fix and hash-approve unconditional reimport.
    import ImportMatureFir
    text=(ROOT/"Scripts/ImportMatureFir.py").read_text()
    assert "if mesh is None:" not in text, "HOLD: stale fir importer"
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSlope")
    from PopulateAlpine import atmosphere
    atmosphere(unreal.get_editor_subsystem(unreal.EditorActorSubsystem))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

    assert hashlib.sha256((ROOT/"Scripts/ImportMatureFir.py").read_bytes()).hexdigest()=="f4ebb1a80f974f24897866d139692010f281b2c7b0aa8bc9dd272b2a74fa8b2b"
    ImportMatureFir.import_fir()
    assert hashlib.sha256((ROOT/"Scripts/CreateSnowMaterial.py").read_bytes()).hexdigest()=="155f6631c10ad2257d110fdeed365c05d88682d3b5329f4fc7d475c87f547475"
    from CreateSnowMaterial import create_snow
    create_snow()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    unreal.log("FALLLINE_FINAL_SNOW_COMPILE_GATE_BEGIN")
    unreal.MaterialEditingLibrary.recompile_material(unreal.load_asset("/Game/Environment/Snow/M_AlpineSnow"))
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    unreal.log("FALLLINE_FINAL_SNOW_COMPILE_GATE_END")
    log=(ROOT/"Saved/Logs/combined-capture.log").read_text(errors="replace")
    final=log.rsplit("FALLLINE_FINAL_SNOW_COMPILE_GATE_BEGIN",1)[-1]
    assert not any(v in final.lower() for v in ["failed to compile material","default material will be used","error [sm","error x3"]), "Final snow shader compile failed"
    # Bounded AA diagnostic explicitly deferred. No resolution/AA cause claim.
    assert hashlib.sha256((ROOT/"Scripts/OptionalVergeDressing.py").read_bytes()).hexdigest()=="3cac91c4b4898438087f6d90b72e8868f0400442082b169ac5720ae39c24fcc9"
    routefile=ROOT/"Saved/Logs/player-route-pass10-worldxy.json"
    assert hashlib.sha256(routefile.read_bytes()).hexdigest()=="3e7d90ceba045ae4f855bec20521df79e54b4839da774ab2817454cf5eae9fc7"
    route=json.loads(routefile.read_text())
    from PrepareRealDEM import height,BOUNDS
    import OptionalVergeDressing
    OptionalVergeDressing.apply(height,BOUNDS,route_xy=[r["xy_cm"] for r in route["samples"]])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    from VerifyImportedSki import verify
    verify()

    # Single process continues into the actual player capture state machine.
    runpy.run_path(str(ROOT/"Scripts/CaptureCombinedRuntime.py"),run_name="__main__")
except Exception:
    import traceback
    (ROOT/"Saved/Logs/combined-bootstrap-error.txt").write_text(traceback.format_exc())
    unreal.log_error(traceback.format_exc())
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
