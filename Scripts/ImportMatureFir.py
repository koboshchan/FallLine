"""Verified CC0 mature fir, independent from parent-owned alpine importer."""
import unreal,json,hashlib
from pathlib import Path
from ImportAlpineAssets import _task,_material,_verify_source,_texture
ROOT=Path('D:/FallLine/SourceAssets/PolyHaven/fir_tree_01')
def import_fir():
    from ValidateAlpineDependencies import validate_alpine_dependencies
    validate_alpine_dependencies()
    _verify_source("fir_tree_01")
    rec=json.loads((ROOT/'single-fir-manifest.json').read_text())
    f=ROOT/rec["output"]
    assert rec.get("roundtrip_verified") and rec.get("mesh_count")==1
    assert f.stat().st_size==rec["size"]
    assert hashlib.sha256(f.read_bytes()).hexdigest()==rec["sha256"]
    path="/Game/Environment/PolyHaven/fir_tree_01"
    options=unreal.FbxImportUI()
    for k,v in {"automated_import_should_detect_type":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,"import_as_skeletal":False,"import_mesh":True,"import_animations":False,"import_materials":False,"import_textures":False,"override_full_name":True}.items():options.set_editor_property(k,v)
    data=options.get_editor_property("static_mesh_import_data")
    for k,v in {"combine_meshes":True,"generate_lightmap_u_vs":False,"auto_generate_collision":False,"build_nanite":False,"convert_scene":True,"convert_scene_unit":True,"import_uniform_scale":1.0}.items():data.set_editor_property(k,v)
    result=_task(f,path,"SM_MatureFirA",unreal.FbxFactory(),options)
    meshes=[x for x in result if isinstance(x,unreal.StaticMesh)]
    assert len(meshes)==1,[x.get_path_name() for x in result]
    mesh=meshes[0]
    materials={p:_material("fir_tree_01",p) for p in ["bark","trunk_a","twig"]}
    assert materials["twig"].get_editor_property("two_sided")
    assert materials["twig"].get_editor_property("blend_mode")==unreal.BlendMode.BLEND_MASKED
    leaf=materials["twig"]
    mel=unreal.MaterialEditingLibrary
    leaf.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    tex=mel.create_material_expression(leaf,unreal.MaterialExpressionTextureSample,-600,1000)
    tex.set_editor_property('texture',_texture('fir_tree_01','twig_diff'))
    tex.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    gain=mel.create_material_expression(leaf,unreal.MaterialExpressionMultiply,-300,1000)
    gain.set_editor_property('const_b',.45)
    assert mel.connect_material_expressions(tex,'RGB',gain,'A')
    assert mel.connect_material_property(gain,'',unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    mel.recompile_material(leaf)
    unreal.EditorAssetLibrary.save_loaded_asset(leaf,False)
    assert leaf.get_editor_property('shading_model')==unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE
    unreal.log("FALLLINE_FIR_THIN_LEAF model=TwoSidedFoliage transmission=diffuse*0.45 alpha_and_DXnormal_unchanged")
    for i,slot in enumerate(mesh.get_editor_property("static_materials")):
        name=str(slot.get_editor_property("material_slot_name")).lower()
        part="twig" if "twig" in name else "trunk_a" if "trunk_a" in name else "bark"
        mesh.set_material(i,materials[part])
        unreal.log("FALLLINE_MATURE_FIR_SLOT "+name+" "+part)
    settings=mesh.get_editor_property("nanite_settings")
    settings.set_editor_property("enabled",True)
    # UE5.8 EngineTypes.h defaults None; preserve open leaf-card area at distance.
    settings.set_editor_property("shape_preservation",unreal.NaniteShapePreservation.PRESERVE_AREA)
    mesh.set_editor_property("nanite_settings",settings)
    assert mesh.get_editor_property("nanite_settings").get_editor_property("enabled"),"Mature fir requires Nanite; refusing fallback"
    assert mesh.get_editor_property("nanite_settings").get_editor_property("shape_preservation")==unreal.NaniteShapePreservation.PRESERVE_AREA,"Fir foliage requires Nanite area preservation"
    unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
    unreal.log("FALLLINE_MATURE_FIR_READY "+mesh.get_path_name())
    return mesh
