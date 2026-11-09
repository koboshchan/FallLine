"""Offline-authored B/C importer. Call only from the sole backed-up editor apply."""
import json,hashlib
from pathlib import Path
import unreal
from ImportAlpineAssets import _task,_material
ROOT=Path("D:/FallLine")
BASE=ROOT/"SourceAssets/PolyHaven/fir_tree_01"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate():
 source=BASE/"fir_tree_01_1k.blend"
 source_sha=sha(source)
 texture=json.loads((BASE/"variants-texture-manifest.json").read_text())
 for r in texture["files"]:
  p=BASE/r["path"];assert p.stat().st_size==r["size"] and sha(p)==r["sha256"]
 rows={}
 for v in "bc":
  r=json.loads((BASE/("single-fir-"+v+"-manifest.json")).read_text())
  f=BASE/r["output"]
  assert r["roundtrip_verified"] and r["uv_exact_roundtrip"] and r["mesh_count"]==1
  assert r["source_sha256"]==source_sha and f.stat().st_size==r["size"] and sha(f)==r["sha256"]
  assert r["object"].lower().endswith(v+"_lod0")
  proof=json.loads((BASE/("original-uv-recovery-"+v+".json")).read_text())
  assert proof["equal_original"] and any("twig" in a["material"] and min(a["uv_std"])>0 for a in proof["parts"])
  rows[v]=r
 assert rows["b"]["sha256"]!=rows["c"]["sha256"]
 return rows
def import_variants():
 rows=validate();out={}
 path="/Game/Environment/PolyHaven/fir_tree_01"
 shared={p:unreal.load_asset(path+"/Materials/M_fir_tree_01_"+p) for p in ["bark","twig"]}
 assert all(shared.values())
 assert shared["twig"].get_editor_property("two_sided")
 assert shared["twig"].get_editor_property("blend_mode")==unreal.BlendMode.BLEND_MASKED
 for v,r in rows.items():
  options=unreal.FbxImportUI()
  for k,value in {"automated_import_should_detect_type":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,"import_as_skeletal":False,"import_mesh":True,"import_animations":False,"import_materials":False,"import_textures":False,"override_full_name":True}.items():options.set_editor_property(k,value)
  data=options.get_editor_property("static_mesh_import_data")
  for k,value in {"combine_meshes":True,"generate_lightmap_u_vs":False,"auto_generate_collision":False,"build_nanite":False,"convert_scene":True,"convert_scene_unit":True,"import_uniform_scale":1.0}.items():data.set_editor_property(k,value)
  meshes=[a for a in _task(BASE/r["output"],path,"SM_MatureFir"+v.upper(),unreal.FbxFactory(),options) if isinstance(a,unreal.StaticMesh)]
  assert len(meshes)==1
  mesh=meshes[0];trunk=_material("fir_tree_01","trunk_"+v)
  for i,slot in enumerate(mesh.get_editor_property("static_materials")):
   name=str(slot.get_editor_property("material_slot_name")).lower()
   material=shared["twig"] if "twig" in name else trunk if "trunk_"+v in name else shared["bark"]
   assert any(p in name for p in ["twig","trunk_"+v,"bark","dead_branches"]),name
   mesh.set_material(i,material)
  settings=mesh.get_editor_property("nanite_settings")
  settings.set_editor_property("enabled",True)
  settings.set_editor_property("shape_preservation",unreal.NaniteShapePreservation.PRESERVE_AREA)
  mesh.set_editor_property("nanite_settings",settings)
  assert mesh.get_editor_property("nanite_settings").get_editor_property("enabled")
  unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
  b=mesh.get_bounding_box();expected=(r["bounds_metres"][1][2]-r["bounds_metres"][0][2])*100
  assert abs((b.max.z-b.min.z)-expected)<1.0,("FBX units",v,expected,b)
  out[v]=mesh
 return out
