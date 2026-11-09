import unreal,json
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TestSlope')
a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
out=[]
for x in a:
 label=x.get_actor_label()
 if isinstance(x,unreal.Landscape) or label in ['Alpine pine 000','Alpine pine 001','Granite outcrop 000']:
  out.append(dict(label=label,location=str(x.get_actor_location()),scale=str(x.get_actor_scale3d()),rotation=str(x.get_actor_rotation()),bounds=str(x.get_actor_bounds(False))))
open('D:/FallLine/Saved/Logs/scene-inspection.json','w').write(json.dumps(out,indent=2))

print("ROTATOR_POSITIONAL",unreal.Rotator(-13,18,0))
print("ROTATOR_KEYWORDS",unreal.Rotator(pitch=-13,yaw=18,roll=0))
