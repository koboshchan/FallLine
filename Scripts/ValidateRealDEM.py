"""Fail-closed DEM prelaunch gate. No acquisition and no editor launch."""
import sys, json, datetime, pathlib, traceback
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Scripts'))
receipt=ROOT/'Saved/Logs/dem-gate.json'
try:
    from PrepareRealDEM import height, BOUNDS, validate_dependencies
    assert callable(height), 'height is not callable'
    assert len(BOUNDS)==4 and BOUNDS[0]<BOUNDS[2] and BOUNDS[1]<BOUNDS[3]
    proof=validate_dependencies()
    assert isinstance(proof,dict) and proof, 'Empty DEM validation proof'
    from ValidateAlpineDependencies import validate_alpine_dependencies
    proof['alpine_assets']=validate_alpine_dependencies(height,BOUNDS)
    result=dict(Status='Passed',Time=datetime.datetime.now(datetime.timezone.utc).isoformat(),Proof=proof)
    receipt.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
except Exception as e:
    receipt.write_text(json.dumps(dict(Status='Failed',Time=datetime.datetime.now(datetime.timezone.utc).isoformat(),Error=str(e)),indent=2),encoding='utf-8')
    traceback.print_exc()
    sys.exit(1)
