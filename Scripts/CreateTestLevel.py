import unreal,sys
sys.path.insert(0,"D:/FallLine/Scripts")
from CreateSnowMaterial import create_snow
from ImportAlpineAssets import import_assets
from ImportSkiGeometry import import_skis
from PopulateAlpine import populate
from PrepareRealDEM import height, BOUNDS, validate_dependencies
from ValidateAlpineDependencies import validate_alpine_dependencies
DEM_PROOF = validate_dependencies()
ALPINE_PROOF = validate_alpine_dependencies(height,BOUNDS)
assert callable(height) and DEM_PROOF, "DEM dependency gate failed"
ski_mesh=import_skis()
assert ski_mesh, "Ski geometry import failed"
world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
assert world
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
slope_class=unreal.load_class(None,"/Script/FallLine.TestSlope")
slope=actors.spawn_actor_from_class(slope_class,unreal.Vector())
slope.set_actor_label("Fall Line - Alpine Basin")
for component in slope.get_components_by_class(unreal.StaticMeshComponent):
    component.set_visibility(False, True)
    component.set_hidden_in_game(True, True)
snow=create_snow()
mountain=unreal.MountainBuilder.create_mountain(world,snow)
assert mountain
pine,rock=import_assets()
populate(pine,rock,surface_sampler=height,bounds=BOUNDS)
start=actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(-8500,0,height(-8500,0)+110))
start.set_actor_label("Run start")
unreal.EditorAssetLibrary.save_directory("/Game")
assert unreal.EditorLoadingAndSavingUtils.save_map(world,"/Game/Maps/TestSlope")
# Verify actual world collision at the spawn and the smoke route, not just a height formula.
import json
from PrepareRealDEM import height
samples=[]
for x,y in [(-8500,0),(-2500,0),(1000,2200),(0,5500),(10000,-5500)]:
    hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,height(x,y)+3000),unreal.Vector(x,y,height(x,y)-3000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE,True)
    assert hit, 'Missing terrain collision at '+str((x,y))
    z=hit.to_tuple()[5].z
    samples.append(dict(x=x,y=y,actual_z=z,expected_z=height(x,y),error_cm=z-height(x,y)))
    assert abs(z-height(x,y))<12, str(samples[-1])
open('D:/FallLine/Saved/Logs/terrain-proof.json','w').write(json.dumps(samples,indent=2))
unreal.log("FALLLINE_MAP_SAVED /Game/Maps/TestSlope REAL_DEM")
