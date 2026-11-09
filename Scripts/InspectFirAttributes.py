import bpy,json
from pathlib import Path
r=Path("D:/FallLine/SourceAssets/PolyHaven/fir_tree_01")
bpy.ops.wm.open_mainfile(filepath=str(r/"fir_tree_01_1k.blend"))
out={}
for name in ["fir_tree_01_a_LOD0","fir_tree_01_twig_main_a"]:
 o=bpy.data.objects[name]
 out[name]={"attributes":[{"name":a.name,"domain":a.domain,"type":a.data_type,"count":len(a.data)} for a in o.data.attributes],"modifiers":[{"name":m.name,"type":m.type} for m in o.modifiers]}
 for a in o.data.attributes:
  if "uv" in a.name.lower():out[name][a.name]=str(a.data[0]) if len(a.data) else ""
Path("D:/FallLine/Saved/Logs/fir-attributes.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out),flush=True)
