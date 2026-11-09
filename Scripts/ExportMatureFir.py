"""Derive a single green fir from original CC0 blend UV attributes; run with Blender 4.4."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/FallLine/SourceAssets/PolyHaven/fir_tree_01')
source=ROOT/'fir_tree_01_1k.blend';output=ROOT/'fir_single_a.fbx'
manifest=json.loads((ROOT/'blend-source-manifest.json').read_text())
rec=next(f for f in manifest['files'] if f['path']==source.name)
assert source.stat().st_size==rec['size']
assert hashlib.md5(source.read_bytes()).hexdigest()==rec['md5']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
print('FIR_SOURCE_MESHES',[(o.name,len(o.data.polygons),list(o.location)) for o in meshes],flush=True)
candidates=[o for o in meshes if o.name.lower().endswith('a_lod0')]
assert len(candidates)==1,[o.name for o in meshes]
tree=candidates[0]
# Exact author UVMap is CORNER FLOAT_VECTOR; FBX needs a true FLOAT2 UV layer.
import numpy as np,sys
sys.path.insert(0,'D:/FallLine/Scripts')
from FirUVProof import prove
attr=tree.data.attributes['UVMap']
assert attr.domain=='CORNER' and attr.data_type=='FLOAT_VECTOR'
coords=np.empty(len(attr.data)*3,dtype=np.float32)
attr.data.foreach_get('vector',coords)
coords=coords.reshape(-1,3)
assert np.isfinite(coords).all()
attr.name='AuthorUVVectorPreserved'
uv=tree.data.uv_layers.new(name='UVMap')
uv.data.foreach_set('uv',coords[:,:2].copy().ravel())
recovered=np.empty(len(uv.data)*2,dtype=np.float32);uv.data.foreach_get('uv',recovered)
assert np.array_equal(recovered.reshape(-1,2),coords[:,:2])
proof=prove(tree,ROOT/'textures/fir_tree_01_twig_alpha_1k.png')
(ROOT/'original-uv-recovery.json').write_text(json.dumps({'method':'author CORNER FLOAT_VECTOR UVMap.xy copied exactly to FLOAT2; no projection','equal_original':True,'parts':proof},indent=2))
print('FIR_ORIGINAL_UV_PROOF',json.dumps(proof),flush=True)

for o in bpy.context.scene.objects:o.select_set(False)
tree.select_set(True);bpy.context.view_layer.objects.active=tree
# FBX original a-tree local origin is the trunk axis. Remove the layout translation.
tree.location.x=0;tree.location.y=0
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
lo=min(v.co.z for v in tree.data.vertices);tree.location.z=-lo
before=len(tree.data.polygons)
if before>650000:
 mod=tree.modifiers.new('Forest mesh reduction','DECIMATE')
 mod.ratio=min(1,650000/before)
 bpy.ops.object.modifier_apply(modifier=mod.name)
# Persist exact final export corner UV sequence for independent FBX roundtrip.
u=tree.data.uv_layers.active
arr=np.empty(len(u.data)*2,dtype=np.float32);u.data.foreach_get('uv',arr)
np.save(ROOT/'fir-export-corner-uv.npy',arr.reshape(-1,2))
bpy.ops.export_scene.fbx(filepath=str(output),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='RELATIVE',embed_textures=False,global_scale=1,apply_unit_scale=True,axis_forward='-Z',axis_up='Y')
receipt={'source':source.name,'license':'CC0','source_url':'https://polyhaven.com/a/fir_tree_01','output':output.name,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'size':output.stat().st_size,'object':tree.name,'polygons_before':before,'polygons_after':len(tree.data.polygons),'materials':[s.material.name for s in tree.material_slots],'bounds_metres':[[min((tree.matrix_world @ Vector(v))[i] for v in tree.bound_box) for i in range(3)],[max((tree.matrix_world @ Vector(v))[i] for v in tree.bound_box) for i in range(3)]],'origin_cm_in_ue':'FBX unit conversion, trunk x/y zero, root bottom z zero'}
(ROOT/'single-fir-manifest.json').write_text(json.dumps(receipt,indent=2))
print('FIR_SINGLE_EXPORTED',json.dumps(receipt),flush=True)
