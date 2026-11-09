import bpy,json
from pathlib import Path
r=Path("D:/FallLine/SourceAssets/PolyHaven/fir_tree_01")
bpy.ops.wm.open_mainfile(filepath=str(r/"fir_tree_01_1k.blend"))
m=bpy.data.materials['fir_tree_01_twig']
out={"nodes":[{"name":n.name,"type":n.type,"image":n.image.filepath if n.type=='TEX_IMAGE' and n.image else None,"inputs":[(i.name,str(i.default_value)) for i in n.inputs if hasattr(i,"default_value") and i.name in ['Alpha','Roughness']]} for n in m.node_tree.nodes],"links":[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]}
Path("D:/FallLine/Saved/Logs/fir-material.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out),flush=True)
