"""Import the vendored CC0 Poly Haven pine and boulder inside Unreal Editor.

Call import_assets() after the project/editor build, before map population.
Returns (pine_mesh, rock_mesh), both unreal.StaticMesh assets. Does not edit
levels, actors, project settings, or launch any external process.
Source manifests and download receipts live in SourceAssets/PolyHaven.
Pine uses the verified single-a Blender derivative, never the three-tree strip.
Generate it first with Scripts/ExportSinglePine.py using Blender.
"""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path("D:/FallLine")
SOURCE = PROJECT / "SourceAssets/PolyHaven"
CONTENT = "/Game/Environment/PolyHaven"
ASSET_NAMES = {"pine_sapling_medium": "SM_PineSingleA",
               "boulder_01": "SM_Boulder01"}


def _verify_source(asset_id):
    folder = SOURCE / asset_id
    data = json.loads((folder / "source-manifest.json").read_text())
    for item in data["files"]:
        path = folder / item["path"]
        if not path.is_file() or path.stat().st_size != item["size"]:
            raise RuntimeError("Incomplete alpine download: " + str(path))
        with path.open("rb") as stream:
            hasher = hashlib.md5()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
            digest = hasher.hexdigest()
        if digest != item["md5"]:
            raise RuntimeError("Alpine source checksum mismatch: " + str(path))
    return data


def _verify_single_pine():
    folder = SOURCE / "pine_sapling_medium"
    receipt = json.loads((folder / "single-pine-manifest.json").read_text())
    path = folder / "pine_single_a.fbx"
    if receipt["output"] != path.name or not receipt["roundtrip_verified"]:
        raise RuntimeError("Invalid single-pine derivation receipt")
    if not path.is_file() or path.stat().st_size != receipt["size"]:
        raise RuntimeError("Run Scripts/ExportSinglePine.py with Blender first")
    with path.open("rb") as stream:
        hasher = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    if hasher.hexdigest() != receipt["sha256"]:
        raise RuntimeError("Single-pine export checksum mismatch")


def _task(filename, destination, name, factory=None, options=None):
    task = unreal.AssetImportTask()
    for key, value in {
        "filename": str(filename), "destination_path": destination,
        "destination_name": name, "automated": True,
        "replace_existing": True, "replace_existing_settings": True,
        "save": True,
    }.items():
        # The Python spelling of the C++ bAsync property is async_.
        task.set_editor_property(key, value)
    if factory is not None:
        task.set_editor_property("factory", factory)
    if options is not None:
        task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.get_objects())


def _texture(asset_id, suffix, normal=False, linear=False):
    folder = SOURCE / asset_id / "textures"
    files = list(folder.glob("*_" + suffix + "_1k.png"))
    if len(files) != 1:
        raise RuntimeError("Expected one alpine texture: " + str(folder / suffix))
    filename = files[0]
    destination = CONTENT + "/" + asset_id + "/Textures"
    asset_path = destination + "/" + filename.stem
    texture = unreal.load_asset(asset_path)
    if texture is None:
        imported = _task(filename, destination, filename.stem,
                         unreal.TextureFactory())
        texture = next((x for x in imported if isinstance(x, unreal.Texture2D)), None)
    if texture is None:
        raise RuntimeError("Texture import failed: " + str(filename))
    texture.set_editor_property("srgb", not (normal or linear))
    if normal:
        texture.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_NORMALMAP)
    elif linear:
        texture.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_loaded_asset(texture, False)
    return texture


def _material(asset_id, part):
    folder = CONTENT + "/" + asset_id + "/Materials"
    name = "M_" + asset_id + ("_" + part if part else "")
    path = folder + "/" + name
    material = unreal.load_asset(path)
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError("Could not create " + path)
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions(material)
    twig = part == "twig"
    material.set_editor_property("two_sided", twig)
    material.set_editor_property("blend_mode",
                                unreal.BlendMode.BLEND_MASKED if twig
                                else unreal.BlendMode.BLEND_OPAQUE)
    if twig:
        material.set_editor_property("opacity_mask_clip_value", 0.33)
    prefix = part + "_" if part else ""
    specs = [
        ("diff", unreal.MaterialProperty.MP_BASE_COLOR, "RGB", False, False),
        ("nor_dx", unreal.MaterialProperty.MP_NORMAL, "RGB", True, False),
        ("rough", unreal.MaterialProperty.MP_ROUGHNESS, "R", False, True),
    ]
    if twig:
        specs.append(("alpha", unreal.MaterialProperty.MP_OPACITY_MASK,
                      "R", False, True))
    for index, (suffix, prop, output, normal, linear) in enumerate(specs):
        texture = _texture(asset_id, prefix + suffix, normal, linear)
        node = mel.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -400, index * 240)
        node.set_editor_property("texture", texture)
        node.set_editor_property(
            "sampler_type",
            unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else
            unreal.MaterialSamplerType.SAMPLERTYPE_MASKS if linear else
            unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        if not mel.connect_material_property(node, output, prop):
            raise RuntimeError("Could not connect " + path + " " + suffix)
    # UE5.8 RecompileMaterial returns void. Shader success is validated by
    # the rendered capture log, not by treating this return value as errors.
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, False)
    return material


def _mesh(asset_id):
    destination = CONTENT + "/" + asset_id
    name = ASSET_NAMES[asset_id]
    path = destination + "/" + name
    mesh = unreal.load_asset(path)
    if mesh is None:
        options = unreal.FbxImportUI()
        for key, value in {
            "automated_import_should_detect_type": False,
            "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
            "import_as_skeletal": False, "import_mesh": True,
            "import_animations": False, "import_materials": False,
            "import_textures": False, "override_full_name": True,
        }.items():
            options.set_editor_property(key, value)
        data = options.get_editor_property("static_mesh_import_data")
        for key, value in {
            "combine_meshes": True, "generate_lightmap_u_vs": False,
            "auto_generate_collision": False, "build_nanite": False,
            "convert_scene": True, "convert_scene_unit": True,
            "import_uniform_scale": 1.0,
        }.items():
            data.set_editor_property(key, value)
        # UE5.8 AssetTools.cpp explicitly bypasses Interchange whenever a
        # specific UFactory is supplied. No global CVars/settings changed.
        filename = ("pine_single_a.fbx" if asset_id == "pine_sapling_medium"
                    else asset_id + "_1k.fbx")
        imported = _task(SOURCE / asset_id / filename,
                         destination, name, unreal.FbxFactory(), options)
        meshes = [x for x in imported if isinstance(x, unreal.StaticMesh)]
        if len(meshes) != 1:
            raise RuntimeError("Expected one combined mesh for " + asset_id +
                               ", got " + str([x.get_path_name() for x in meshes]))
        mesh = meshes[0]
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError("Not a static mesh: " + path)
    parts = ["bark", "twig"] if asset_id == "pine_sapling_medium" else [""]
    materials = {part: _material(asset_id, part) for part in parts}
    slots = list(mesh.get_editor_property("static_materials"))
    if not slots:
        raise RuntimeError("No FBX material slots: " + asset_id)
    for index, slot in enumerate(slots):
        slot_name = (str(slot.get_editor_property("material_slot_name")) + " " +
                     str(slot.get_editor_property("imported_material_slot_name"))).lower()
        if asset_id == "pine_sapling_medium":
            part = next((p for p in parts if p in slot_name), None)
            # The FBX dead-branch slot is opaque woody geometry, not needles.
            if part is None and "dead_branches" in slot_name:
                part = "bark"
            if part is None:
                raise RuntimeError("Unrecognized pine material slot: " + slot_name)
        else:
            part = ""
        mesh.set_material(index, materials[part])
        unreal.log("FALLLINE_ALPINE_SLOT " + asset_id + " " +
                   str(index) + " " + slot_name + " " + part)
    # Commandlet mode does not instantiate StaticMeshEditorSubsystem.
    # UStaticMesh exposes NaniteSettings as an EditAnywhere property; Python's
    # setter issues PostEditChangeProperty, rebuilding the mesh on save.
    settings = mesh.get_editor_property("nanite_settings")
    settings.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", settings)
    if not mesh.get_editor_property("nanite_settings").get_editor_property("enabled"):
        raise RuntimeError("Nanite did not enable: " + path)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    unreal.log("FALLLINE_ALPINE_MESH_READY " + mesh.get_path_name())
    return mesh


def import_assets():
    """Return (pine_mesh, rock_mesh). Source checksums must pass first.

    Meshes use source FBX units converted into UE centimetres. No automatic
    mesh collision is generated. The map owner should add deliberate gameplay
    collision (for example trunk capsules), rather than a convex needle crown.
    """
    for asset_id in ASSET_NAMES:
        _verify_source(asset_id)
    _verify_single_pine()
    pine = _mesh("pine_sapling_medium")
    rock = _mesh("boulder_01")
    unreal.log("FALLLINE_ALPINE_ASSETS_READY")
    return pine, rock
