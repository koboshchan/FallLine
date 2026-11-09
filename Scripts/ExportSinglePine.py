"""Derive one origin-centred tree from the unchanged CC0 Poly Haven FBX.
Run with Blender --background --factory-startup --python this_script.
API reference https://docs.blender.org/api/current/bpy.ops.export_scene.html
"""
import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

FOLDER = Path("D:/FallLine/SourceAssets/PolyHaven/pine_sapling_medium")
SOURCE = FOLDER / "pine_sapling_medium_1k.fbx"
OUTPUT = FOLDER / "pine_single_a.fbx"


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bounds(obj):
    points = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


manifest = json.loads((FOLDER / "source-manifest.json").read_text())
record = next(f for f in manifest["files"] if f["path"] == SOURCE.name)
assert SOURCE.stat().st_size == record["size"]
assert digest(SOURCE, "md5") == record["md5"]
source_sha = digest(SOURCE)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SOURCE))
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
print("SOURCE_OBJECTS", [(o.name, list(o.location), bounds(o)) for o in meshes])
candidates = [o for o in meshes if o.name.endswith("a_LOD0")]
assert len(candidates) == 1, [o.name for o in meshes]
tree = candidates[0]
assert tree.location.length < 0.001, list(tree.location)
before = bounds(tree)
materials = [s.material.name for s in tree.material_slots]
counts = [len(tree.data.vertices), len(tree.data.polygons)]
for obj in bpy.context.scene.objects:
    obj.select_set(False)
tree.select_set(True)
bpy.context.view_layer.objects.active = tree
assert bpy.ops.export_scene.fbx(
    filepath=str(OUTPUT), use_selection=True, object_types={"MESH"},
    bake_anim=False, path_mode="RELATIVE", embed_textures=False,
    global_scale=1.0, apply_unit_scale=True,
    axis_forward="-Z", axis_up="Y") == {"FINISHED"}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(OUTPUT))
exported = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert len(exported) == 1, [o.name for o in exported]
check = exported[0]
after = bounds(check)
assert max(abs(a-b) for aa,bb in zip(before,after) for a,b in zip(aa,bb)) < 0.001
assert [s.material.name for s in check.material_slots] == materials
assert [len(check.data.vertices), len(check.data.polygons)] == counts
assert check.location.length < 0.001
assert digest(SOURCE) == source_sha
receipt = {
    "source": SOURCE.name, "source_sha256": source_sha,
    "selected_object": check.name,
    "output": OUTPUT.name, "size": OUTPUT.stat().st_size,
    "sha256": digest(OUTPUT), "bounds_metres": after,
    "vertices": counts[0], "polygons": counts[1],
    "materials": materials, "blender": bpy.app.version_string,
    "roundtrip_verified": True, "origin_metres": list(check.location),
    "recipe": "Scripts/ExportSinglePine.py",
}
(FOLDER / "single-pine-manifest.json").write_text(json.dumps(receipt, indent=2)+"\n")
print("SINGLE_PINE_VERIFIED", json.dumps(receipt))
