import unreal,time,os,json
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/TestSlope")
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
receipt=[]
for actor in actors.get_all_level_actors():
    label=actor.get_actor_label()
    if label in ['Alpine pine 000','Alpine pine 155','Alpine pine 156','Alpine Basin - 2km Landscape']:
        receipt.append(dict(label=label,location=str(actor.get_actor_location()),rotation=str(actor.get_actor_rotation()),scale=str(actor.get_actor_scale3d()),bounds=str(actor.get_actor_bounds(False))))
open('D:/FallLine/Saved/Logs/capture-scene-proof.json','w').write(json.dumps(receipt,indent=2))
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.SystemLibrary.execute_console_command(world,"r.SetRes 1600x900w")
unreal.SystemLibrary.execute_console_command(world,"sg.GlobalIlluminationQuality 2")
unreal.SystemLibrary.execute_console_command(world,"sg.ReflectionQuality 2")
unreal.SystemLibrary.execute_console_command(world,"sg.ShadowQuality 2")
out="D:/FallLine/Saved/Screenshots/AlpineCorrected"
os.makedirs(out,exist_ok=True)
import sys
sys.path.insert(0,"D:/FallLine/Scripts")
from PrepareRealDEM import height, BOUNDS, validate_dependencies
from AlpineViewpoints import shots as alpine_shots
validate_dependencies()
viewpoints=alpine_shots(height,BOUNDS)
open('D:/FallLine/Saved/Logs/alpine-viewpoints.json','w').write(json.dumps(viewpoints,indent=2))
shots=[(v['name'],unreal.Vector(*v['location']),unreal.Rotator(pitch=v['rotation'][0],yaw=v['rotation'][1],roll=v['rotation'][2])) for v in viewpoints]

state={"index":0,"time":time.monotonic(),"task":None,"handle":None,"busy":False}
def frame(dt):
    if state["busy"] or time.monotonic()-state["time"]<25: return
    task=state["task"]
    if task and not task.is_task_done(): return
    i=state["index"]
    if i>=len(shots):
        unreal.unregister_slate_post_tick_callback(state["handle"])
        open(out+"/capture-result.json","w").write(json.dumps({"success":True,"shots":[s[0] for s in shots]}))
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        return
    state["busy"]=True
    name,pos,rot=shots[i]
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(pos,rot)
    state["task"]=unreal.AutomationLibrary.take_high_res_screenshot(1600,900,out+"/"+name+".png",delay=3.0)
    state["index"]+=1
    state["time"]=time.monotonic()
    state["busy"]=False
state["handle"]=unreal.register_slate_post_tick_callback(frame)
