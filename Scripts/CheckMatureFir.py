"""Offline Blender FBX derivative round-trip verification."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path('D:/FallLine/SourceAssets/PolyHaven/fir_tree_01')
r=json.loads((root/'single-fir-manifest.json').read_text())
p=root/r['output']
assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(p))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==1,[o.name for o in meshes]
tree=meshes[0]
points=[tree.matrix_world @ Vector(v) for v in tree.bound_box]
lo=[min(v[i] for v in points) for i in range(3)]
hi=[max(v[i] for v in points) for i in range(3)]
assert abs(lo[2])<.01,(lo,hi)
assert 4<hi[2]-lo[2]<40,(lo,hi)
import sys
sys.path.insert(0,'D:/FallLine/Scripts')
from FirUVProof import prove
import numpy as np
expected=np.load(root/'fir-export-corner-uv.npy')
u=tree.data.uv_layers.active
assert u and len(u.data)==len(expected),"Roundtrip corner count changed"
actual=np.empty(len(u.data)*2,dtype=np.float32);u.data.foreach_get('uv',actual);actual=actual.reshape(-1,2)
assert np.array_equal(expected,actual),"Roundtrip UV corner order or XY changed"
r['uv_corner_count']=len(actual)
r['uv_corner_order_exact']=True
r['uv_xy_roundtrip_max_error']=float(np.max(np.abs(expected-actual)))
proof=prove(tree,root/'textures/fir_tree_01_twig_alpha_1k.png')
r['uv_roundtrip_verified']=True
r['uv_parts']=proof
r['uv_recovery_source']='fir_tree_01_1k.blend:CORNER FLOAT_VECTOR UVMap.xy'
assert [s.material.name for s in tree.material_slots]==['fir_tree_01_bark','fir_tree_01_trunk_a','fir_tree_01_twig','fir_tree_01_dead_branches']
r['roundtrip_verified']=True
r['bounds_metres']=[lo,hi]
r['height_metres']=hi[2]-lo[2]
r['mesh_count']=len(meshes)
r['materials']=[s.material.name for s in tree.material_slots]
(root/'single-fir-manifest.json').write_text(json.dumps(r,indent=2))
print('FIR_ROUNDTRIP_VERIFIED',json.dumps(r),flush=True)
