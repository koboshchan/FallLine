"""Read-only derivative topology/material/UV inspection in Blender."""
import bpy,json
from pathlib import Path
from collections import Counter
root=Path('D:/FallLine/SourceAssets/PolyHaven/fir_tree_01')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(root/'fir_single_a.fbx'))
out=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 counts=Counter(p.material_index for p in o.data.polygons)
 uv=o.data.uv_layers.active
 parts=[]
 for idx,n in counts.items():
  polys=[p for p in o.data.polygons if p.material_index==idx]
  coords=[uv.data[li].uv[:] for p in polys for li in p.loop_indices] if uv else []
  parts.append({'material':o.material_slots[idx].material.name,'polygons':n,'surface_area_m2':sum(p.area for p in polys),'uv_range':[[min(v[k] for v in coords) for k in range(2)],[max(v[k] for v in coords) for k in range(2)]] if coords else None})
 out.append({'object':o.name,'parts':parts})
Path('D:/FallLine/Saved/Logs/fir-offline-inspection.json').write_text(json.dumps(out,indent=2))
print('FIR_OFFLINE_INSPECTION',json.dumps(out),flush=True)
