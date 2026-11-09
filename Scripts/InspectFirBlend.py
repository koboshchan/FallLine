import bpy,json
from pathlib import Path
r=Path("D:/FallLine/SourceAssets/PolyHaven/fir_tree_01")
bpy.ops.wm.open_mainfile(filepath=str(r/"fir_tree_01_1k.blend"))
out=[{"name":o.name,"type":o.type,"polygons":len(o.data.polygons),"uv_layers":[u.name for u in o.data.uv_layers],"materials":[m.name if m else None for m in o.data.materials]} for o in bpy.data.objects if o.type=="MESH"]
Path("D:/FallLine/Saved/Logs/fir-blend-uv.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out),flush=True)
