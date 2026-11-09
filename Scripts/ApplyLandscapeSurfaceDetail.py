"""Visual-only native Landscape LOD0 clamp. Owner invokes after backup; never saves."""
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path("D:/FallLine")
DEM = ROOT / "SourceAssets/DEM/verbier.r16"

def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _transform(actor):
    t = actor.get_actor_transform()
    return [getattr(v, k) for v, axes in ((t.translation, "xyz"),
            (t.rotation, "xyzw"), (t.scale3d, "xyz")) for k in axes]

def _collision(actor):
    return sorted((c.get_path_name(), str(c.get_collision_enabled()),
                   str(c.get_collision_profile_name()))
                  for c in actor.get_components_by_class(unreal.PrimitiveComponent))

def apply():
    """Apply to the EXISTING saved landscape, not CreateTestLevel or regeneration."""
    assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None, "PIE active"
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    landscapes = [a for a in actors if isinstance(a, unreal.LandscapeProxy)]
    assert len(landscapes) == 1 and isinstance(landscapes[0], unreal.Landscape), "Expected actual single ALandscape"
    land = landscapes[0]
    assert "Verbier" in land.get_actor_label(), "Unexpected landscape"
    assert not land.get_editor_property("enable_nanite"), "Nanite already enabled; native LOD clamp is not effective there"
    before = dict(transform=_transform(land), collision=_collision(land), dem_sha256=_sha(DEM))
    old_lod = land.get_editor_property("max_lod_level")
    land.set_editor_property("max_lod_level", 0)
    assert land.get_editor_property("max_lod_level") == 0
    after = dict(transform=_transform(land), collision=_collision(land), dem_sha256=_sha(DEM))
    assert before == after, "Terrain preservation failed; do not save"
    result = dict(passed=True, saved=False, actor=land.get_path_name(),
                  old_max_lod_level=old_lod, max_lod_level=0,
                  preservation=after,
                  limitation="Native 5m DEM grid retained. No new geometric detail or silhouette smoothing claimed.",
                  tradeoff="All landscape components retain finest native mesh LOD; higher GPU geometry cost.")
    out = ROOT / "Saved/Logs/LandscapeSurfaceDetail"
    out.mkdir(parents=True, exist_ok=True)
    (out / "apply.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    return result
