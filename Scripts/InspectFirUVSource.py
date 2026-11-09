"""Read-only source versus derivative UV layer count."""
import bpy,json
from pathlib import Path
root=Path("D:/FallLine/SourceAssets/PolyHaven/fir_tree_01")
out={}
for filename in ["fir_single_a.fbx","fir_tree_01_1k.fbx"]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.fbx(filepath=str(root/filename))
 out[filename]=[{"name":o.name,"vertices":len(o.data.vertices),"uv_layers":[{"name":u.name,"loops":len(u.data)} for u in o.data.uv_layers]} for o in bpy.context.scene.objects if o.type=="MESH"]
 print(filename,json.dumps(out[filename]),flush=True)
Path("D:/FallLine/Saved/Logs/fir-source-uv.json").write_text(json.dumps(out,indent=2))
