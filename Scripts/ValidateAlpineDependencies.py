"""Strict stdlib preflight. No Unreal import, no generation, no acquisition.
validate_alpine_dependencies(height=None,bounds=None) -> evidence dict.
With supplied sampler, validates exact world-cm bounds and finite probe heights.
"""
from pathlib import Path
import hashlib,json,math
ROOT=Path("D:/FallLine")
def digest(path,kind):
    h=hashlib.new(kind)
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()
def validate_alpine_dependencies(height=None,bounds=None):
    base=ROOT/"SourceAssets/PolyHaven/fir_tree_01"
    m=json.loads((base/"source-manifest.json").read_text())
    assert m["asset"]=="fir_tree_01" and m["license"]=="CC0"
    assert m["license_url"]=="https://polyhaven.com/license"
    assert m["source"]=="https://polyhaven.com/a/fir_tree_01"
    verified=[]
    for item in m["files"]:
        relative=Path(item["path"])
        assert not relative.is_absolute() and ".." not in relative.parts
        p=base/relative
        assert p.is_file() and p.stat().st_size==item["size"],str(p)
        assert digest(p,"md5")==item["md5"],"MD5 mismatch "+str(p)
        verified.append({"path":item["path"],"size":p.stat().st_size,"sha256":digest(p,"sha256")})
    rec=json.loads((base/"single-fir-manifest.json").read_text())
    from FirUVGate import validate_uv
    validate_uv(base,rec)
    assert rec["license"]=="CC0" and rec["source_url"]==m["source"]
    assert rec["output"]=="fir_single_a.fbx" and rec["roundtrip_verified"] and rec["mesh_count"]==1
    p=base/rec["output"]
    assert p.is_file() and p.stat().st_size==rec["size"]
    assert digest(p,"sha256")==rec["sha256"],"Fir derivative SHA mismatch"
    assert 4<rec["height_metres"]<40 and rec["polygons_after"]<1500000
    assert rec["bounds_metres"][0][2]>-.01
    # Gate actual texture files too, before any engine importer work.
    for suffix in ["diff","nor_dx","rough"]:
        p=ROOT/("SourceAssets/PolyHaven/snow_02_"+suffix+"_2k.jpg")
        assert p.is_file() and p.stat().st_size>100000,str(p)
        assert p.open("rb").read(2)==b"\xff\xd8",str(p)
    b=ROOT/"SourceAssets/PolyHaven/boulder_01"
    bm=json.loads((b/"source-manifest.json").read_text())
    for item in bm["files"]:
        p=b/item["path"]
        assert p.is_file() and p.stat().st_size==item["size"] and digest(p,"md5")==item["md5"],str(p)
    result={"passed":True,"unreal_launched":False,"license":"CC0","fir_files":verified,"derivative":rec,"sampler_validated":False}
    if height is not None or bounds is not None:
        assert callable(height) and bounds is not None and len(bounds)==4
        xmin,ymin,xmax,ymax=map(float,bounds)
        assert all(map(math.isfinite,(xmin,ymin,xmax,ymax))) and xmin<xmax and ymin<ymax
        assert xmin<=-8500<=xmax and ymin<=0<=ymax
        probes=[(-8500,0),(xmin,ymin),(xmax,ymax),((xmin+xmax)/2,(ymin+ymax)/2)]
        z=[float(height(x,y)) for x,y in probes]
        assert all(map(math.isfinite,z)),"Nonfinite supplied DEM height"
        result.update(sampler_validated=True,bounds=list(bounds),probe_xy=probes,probe_z_cm=z)
    return result
if __name__=="__main__":
    import sys
    # Parent can request exact DEM callable contract in a standalone prelaunch gate.
    if "--dem" in sys.argv:
        from PrepareRealDEM import height,BOUNDS
        result=validate_alpine_dependencies(height,BOUNDS)
    else:result=validate_alpine_dependencies()
    (ROOT/"Saved/Logs/alpine-dependencies.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({"passed":True,"sampler_validated":result["sampler_validated"],"derivative_sha256":result["derivative"]["sha256"]}))
