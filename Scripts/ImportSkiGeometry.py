"""Call import_skis() in parent's map-generation process before capture.
No level/project/physics edits. Native FbxFactory supports OBJ (5.8 source).
"""
from pathlib import Path
import unreal
def import_skis():
    source=Path("D:/FallLine/SourceAssets/Skis/ski.obj")
    task=unreal.AssetImportTask()
    task.filename=str(source)
    task.destination_path="/Game/Equipment/Skis"
    task.destination_name="SM_AlpineSki"
    task.automated=True
    task.replace_existing=True
    task.save=True
    task.factory=unreal.FbxFactory()
    options=unreal.FbxImportUI()
    options.automated_import_should_detect_type=False
    options.mesh_type_to_import=unreal.FBXImportType.FBXIT_STATIC_MESH
    options.import_as_skeletal=False
    options.import_mesh=True
    options.import_materials=False
    options.import_textures=False
    options.import_animations=False
    options.override_full_name=True
    data=options.static_mesh_import_data
    for key,value in dict(combine_meshes=True,auto_generate_collision=False,
                          generate_lightmap_u_vs=False,build_nanite=False,
                          convert_scene=False,convert_scene_unit=False,
                          import_uniform_scale=1.0).items():
        data.set_editor_property(key,value)
    task.options=options
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    meshes=[o for o in task.get_objects() if isinstance(o,unreal.StaticMesh)]
    if len(meshes)!=1:
        raise RuntimeError("Expected one combined ski mesh")
    mesh=meshes[0]
    colors=dict(OrangeTopsheet=(.95,.12,.02),GraphiteBase=(.022,.03,.045),
                SteelEdge=(.46,.52,.59))
    slots=list(mesh.static_materials)
    labels=[str(s.material_slot_name) for s in slots]
    if len(slots)!=3 or any(not any(k.lower() in label.lower() for label in labels) for k in colors):
        raise RuntimeError("Ski OBJ lost named material slots: "+str(labels))
    for i,slot in enumerate(slots):
        label=str(slot.material_slot_name)
        key=next((k for k in colors if k.lower() in label.lower()),None)
        if key is None:
            raise RuntimeError("Unexpected ski slot "+label)
        name="M_Ski_"+key;folder="/Game/Equipment/Skis"
        mat=unreal.load_asset(folder+"/"+name)
        if mat is None:
            mat=tools.create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew())
        mel=unreal.MaterialEditingLibrary
        mel.delete_all_material_expressions(mat)
        color=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-300,0)
        color.set_editor_property("constant",unreal.LinearColor(*colors[key],1))
        mel.connect_material_property(color,"",unreal.MaterialProperty.MP_BASE_COLOR)
        rough=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-300,200)
        rough.set_editor_property("r",.26 if key=="SteelEdge" else .38)
        mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS)
        metal=mel.create_material_expression(mat,unreal.MaterialExpressionConstant,-300,400)
        metal.set_editor_property("r",.85 if key=="SteelEdge" else 0)
        mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC)
        mel.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
        mesh.set_material(i,mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
    bounds=mesh.get_bounding_box()
    extent=bounds.max-bounds.min
    if abs(extent.x-190)>2 or extent.z<10 or extent.z>20:
        raise RuntimeError("Ski import axis/scale incorrect: "+str(bounds))
    unreal.log("FALLLINE_TRUE_SKI_READY "+mesh.get_path_name()+" "+str(bounds))
    return mesh
