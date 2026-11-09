"""Capture the actual PIE pawn through its possessed player viewport.
Runtime-only camera framing and paused pose, no saved level or physics edits.
Requires interactive UnrealEditor.exe, not -game/-nullrhi or a commandlet.
"""
import unreal, time, json, traceback
from pathlib import Path

ROOT = Path("D:/FallLine")
OUT = ROOT / "Saved/Screenshots/ActualPlayer"
OUT.mkdir(parents=True, exist_ok=True)
RUN = "snowdiag-" + str(time.time_ns())
SHOT = OUT / ("player-" + RUN + ".png")
RESULT = OUT / ("capture-result-" + RUN + ".json")
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MODES=["baseline","neutral_detail_normal","unlit_albedo","cliff_mask"]
import sys
sys.path.insert(0,str(ROOT/"Scripts"))
import SnowDiagnostics as diag
state = dict(environment_done=False, ab_view="baseline", phase="startup", began=time.monotonic(), ticks=0, handle=None)
proof = dict(run=RUN, success=False, image_verified=False, screenshot=str(SHOT), mode="PIE possessed SkiPawn, paused settled pose")


def numeric_transform(t):
    return [t.translation.x,t.translation.y,t.translation.z,t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w,t.scale3d.x,t.scale3d.y,t.scale3d.z]
def frozen_snapshot(pawn):
    components=pawn.get_components_by_class(unreal.SceneComponent)
    result=dict(pawn=numeric_transform(pawn.get_actor_transform()),components={c.get_name():numeric_transform(c.get_world_transform()) for c in components if c.get_name() in ("SkierVisual","RiggedSkier","LeftSki","RightSki","ChaosSkiBody")})
    mesh=pawn.get_components_by_class(unreal.PoseableMeshComponent)[0]
    result["bones"]={str(n):numeric_transform(mesh.get_bone_transform_by_name(n,unreal.BoneSpaces.COMPONENT_SPACE)) for n in [mesh.get_bone_name(i) for i in range(mesh.get_num_bones())]}
    return result

def receipt():
    RESULT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

def stop(error=None):
    if (error or state.get("environment_done")) and diag.S:
        try:
            diag.restore()
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            diag.disk()
            proof["restore_graph_disk"]="PASS"
            proof["restore_loading_gate"]="completed"
        except Exception:
            error=(error or "")+" RESTORE FAILURE "+traceback.format_exc()
    if error:
        proof["error"] = error
        unreal.log_error(error)
    receipt()
    # End PIE asynchronously. Release keepalive only after its world is gone.
    state["phase"] = "ending"
    state["end_at"] = time.monotonic()
    level.editor_request_end_play()

def frame_impl(dt):
    try:
        now = time.monotonic()
        phase = state["phase"]
        if phase == "ending":
            if editor.get_game_world() is None and not proof.get("error") and not state.get("environment_done"):
                state.update(phase="environment",environment_index=0,environment_at=now,environment_task=None)
                return
            if editor.get_game_world() is None:
                proof["cleanup_phase"]="Releasing command-line Python keepalive after PIE end request"
                receipt()
                unreal.log("FALLLINE_CAPTURE_RELEASE_KEEPALIVE")
                unreal.EditorPythonScripting.set_keep_python_script_alive(False)
                unreal.unregister_slate_post_tick_callback(state["handle"])
            elif now - state["end_at"] > 45:
                proof["error"] = "PIE did not end normally within 45 seconds"
                proof["success"] = False
                receipt()
                proof["cleanup_phase"]="Releasing command-line Python keepalive after PIE end request"
                receipt()
                unreal.log("FALLLINE_CAPTURE_RELEASE_KEEPALIVE")
                unreal.EditorPythonScripting.set_keep_python_script_alive(False)
                unreal.unregister_slate_post_tick_callback(state["handle"])
            return
        if now - state["began"] > 900:
            stop("Player capture timed out in " + phase)
            return
        log_path=ROOT / "Saved/Logs/snow-diagnostics.log"
        if log_path.exists():
            log_tail=log_path.read_text(errors="replace")
            if any(q in log_tail for q in ["Ensure condition failed:","Fatal error:","Failed to compile Material","Default Material will be used"]):
                stop("Engine ensure/fatal detected during capture; inspect dedicated capture log")
                return
        if phase == "startup":
            if now - state["began"] < 3:
                return
            level.editor_request_begin_play()
            state["phase"] = "wait_pawn"
            return
        if phase == "environment":
            task=state.get("environment_task")
            if task and not task.is_task_done():return
            if now-state["environment_at"]<20:return
            i=state["environment_index"]
            if i>=len(MODES):
                state["environment_done"]=True
                stop()
                return
            mode=MODES[i]
            diag.select(mode,state["diag_metadata"])
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            v=state["overview_camera"]
            editor.set_level_viewport_camera_info(unreal.Vector(*v["location"]),
                unreal.Rotator(pitch=v["rotation"][0],yaw=v["rotation"][1],roll=v["rotation"][2]))
            unreal.SystemLibrary.execute_console_command(editor.get_editor_world(),"r.EyeAdaptationQuality 0")
            state.update(phase="overview_settle",overview_at=now,overview_mode=mode)
            return
        if phase=="overview_settle":
            if now-state["overview_at"]<15:return
            v=state["overview_camera"]
            actual=editor.get_level_viewport_camera_info()
            actual_numeric=[actual[0].x,actual[0].y,actual[0].z,actual[1].pitch,actual[1].yaw,actual[1].roll]
            assert actual_numeric==state.setdefault("overview_actual_camera",actual_numeric),"Overview camera drift"
            path=OUT/("overview-"+state["overview_mode"]+"-"+RUN+".png")
            proof.setdefault("overview_views",{})[state["overview_mode"]]=dict(path=str(path),actual_camera=str(actual),exposure_quality=unreal.SystemLibrary.get_console_variable_int_value("r.EyeAdaptationQuality"))
            assert proof["overview_views"][state["overview_mode"]]["exposure_quality"]==0
            state["environment_task"]=unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),delay=3.0)
            state["environment_index"]+=1
            state.update(phase="environment",environment_at=now)
            receipt()
            return
        world = editor.get_game_world()
        if world is None:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        if pawn is None or pc is None:
            return
        if phase == "wait_pawn":
            if pawn.get_class().get_name() != "SkiPawn":
                stop("Possessed pawn is not SkiPawn: " + pawn.get_class().get_name())
                return
            # Use the DEM-backed PlayerStart supplied by the parent map. Never
            # teleport to the obsolete analytic slope coordinates.
            import sys
            if str(ROOT / "Scripts") not in sys.path:
                sys.path.insert(0, str(ROOT / "Scripts"))
            from PrepareRealDEM import height
            initial = pawn.get_actor_location()
            dem_z = float(height(initial.x, initial.y))
            clearance = initial.z - dem_z
            proof.update(initial_location=str(initial), dem_surface_z_cm=dem_z,
                         initial_origin_dem_clearance_cm=clearance)
            if clearance < -30 or clearance > 500:
                stop("Possessed pawn spawn does not match DEM height: " + str(clearance))
                return
            meshes = pawn.get_components_by_class(unreal.PoseableMeshComponent)
            skis = [c for c in pawn.get_components_by_class(unreal.StaticMeshComponent)
                    if c.get_name() in ("LeftSki", "RightSki")]
            mesh = meshes[0].get_skinned_asset() if meshes else None
            if mesh is None or "SKM_Manny_Simple" not in mesh.get_path_name() or len(skis) != 2:
                stop("Missing real Manny or both ski components")
                return
            ski_assets = [c.get_editor_property("static_mesh") for c in skis]
            if any(m is None or "SM_AlpineSki" not in m.get_path_name() for m in ski_assets):
                stop("Actual curved ski assets missing; cube/empty skis rejected")
                return
            proof.update(pawn=pawn.get_path_name(), mesh=mesh.get_path_name(),
                         skis=[c.get_name() for c in skis],
                         ski_assets=[m.get_path_name() for m in ski_assets])
            # Capture-only three-quarter overhead framing; geometry/physics unchanged.
            # UE5.8 Controller.h SetControlRotation and SpringArmComponent.h
            # TargetArmLength are verified public Blueprint-callable properties.
            boom = pawn.get_components_by_class(unreal.SpringArmComponent)[0]
            boom.set_editor_property("target_arm_length", 460.0)
            boom.set_editor_property("enable_camera_lag", False)
            pc.set_control_rotation(unreal.Rotator(pitch=-28, yaw=-55, roll=0))
            proof["capture_camera_request"] = dict(arm_cm=460.0, pitch=-28, yaw=-55,
                scope="PIE capture only; no saved pawn, physics, input or geometry changes",
                validation="runtime visual inspection pending")
            unreal.SystemLibrary.execute_console_command(world, "r.MotionBlurQuality 0", pc)
            # PIE may start paused. Genuine simulation must advance before pose lock.
            proof["initial_paused"]=unreal.GameplayStatics.is_game_paused(world)
            unreal.GameplayStatics.set_game_paused(world,False)
            proof["unpaused"]=not unreal.GameplayStatics.is_game_paused(world)
            if not proof["unpaused"]:
                stop("Cannot advance real gameplay from paused PIE")
                return
            # Native TestSlope default subobjects reset editor overrides in PIE.
            # Apply the owner's exact visual atmosphere tuning to the actual world.
            from PopulateAlpine import atmosphere
            class RuntimeActors:
                def get_all_level_actors(self):
                    return unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
            atmosphere(RuntimeActors())
            for actor in RuntimeActors().get_all_level_actors():
                for c in actor.get_components_by_class(unreal.SkyAtmosphereComponent):
                    c.set_rayleigh_scattering_scale(.0331);c.set_mie_scattering_scale(.003996)
                for c in actor.get_components_by_class(unreal.ExponentialHeightFogComponent):
                    c.set_fog_density(.0015);c.set_fog_max_opacity(.65)

            state["simulation_samples"]=[]
            # Exact four project-owned TestSlope primitive components only.
            from AuditPlayerVisibility import collect
            proof["before_hide_audit"]=collect(world,pawn,pc)
            for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,"/Script/FallLine.TestSlope")):
                for c in actor.get_components_by_class(unreal.StaticMeshComponent):
                    if c.get_name() in ("Rail","Box","RailEntry","BoxEntry"):
                        assert c.get_editor_property("static_mesh").get_path_name()=="/Engine/BasicShapes/Cube.Cube"
                        collision=c.get_collision_enabled()
                        c.set_hidden_in_game(True,False)
                        c.set_visibility(False,False)
                        assert c.get_collision_enabled()==collision
            receipt()
            state["pose_at"] = now
            state["phase"] = "settle_pose"
            return
        if phase == "settle_pose":
            from AuditPlayerVisibility import sole_clearance
            if len(state["simulation_samples"])<1 or now-state.get("last_sample",0)>.5:
                sample=dict(elapsed=now-state["pose_at"],location=str(pawn.get_actor_location()),
                            velocity=str(pawn.get_velocity()),sole=sole_clearance(world,pawn))
                state["simulation_samples"].append(sample)
                state["last_sample"]=now
                proof["simulation_samples"]=state["simulation_samples"]
                receipt()
            if now-state["pose_at"]<6 or len(state["simulation_samples"])<5:
                return
            # Wait for genuine visually grounded gameplay, never pause mid-flight.
            current=sole_clearance(world,pawn)
            minima=[q["min_dem_clearance_cm"] for q in current["skis"]]
            if any(abs(q)>8 for q in minima):
                if now-state["pose_at"]>15:
                    stop("No genuine ground-contact frame within gameplay window")
                return
            # Optional pause. GameMode can reject it in PIE; no physics edits.
            requested = unreal.GameplayStatics.set_game_paused(world, True)
            paused = unreal.GameplayStatics.is_game_paused(world)
            proof.update(pause_request_return=bool(requested), paused=bool(paused))
            if not paused:
                stop("Pause refused; cannot produce same-frozen-pose A/B")
                return
            proof["frozen_reference"]=frozen_snapshot(pawn)
            previous=json.loads((OUT/"capture-result-1794231917127620600.json").read_text())
            overview=next(v["camera"] for v in previous["environment_shots"] if "overview-" in v["path"])
            state["overview_camera"]=overview
            unreal.SystemLibrary.execute_console_command(world,"r.EyeAdaptationQuality 0",pc)
            exposure=unreal.SystemLibrary.get_console_variable_int_value("r.EyeAdaptationQuality")
            assert exposure==0
            metadata=dict(player=dict(camera=[str(pc.player_camera_manager.get_camera_location()),str(pc.player_camera_manager.get_camera_rotation()),85.0],pose=proof["frozen_reference"],exposure=dict(eye_adaptation_quality=exposure),render_size=[1600,900],settle_policy="240ticks and15seconds after finish_loading"),
                overview=dict(camera=overview,pose="saved editor world; no actor edits",exposure=dict(eye_adaptation_quality=exposure),render_size=[1600,900],settle_policy="15seconds after finish_loading"))
            state["diag_metadata"]=metadata
            diag.begin(metadata)
            diag.select("baseline",metadata)

            from AuditPlayerVisibility import collect
            proof["runtime_audit_initial"] = collect(world,pawn,pc)
            receipt()
            proof["pawn_location"] = str(pawn.get_actor_location())
            proof["pawn_rotation"] = str(pawn.get_actor_rotation())
            proof["velocity_before_pause"] = str(pawn.get_velocity())
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            state.update(phase="render_settle", ticks=0, settled_at=now)
            return
        if phase == "render_settle":
            state["ticks"] += 1
            # At least 240 rendered Slate ticks AND 15 seconds after loading.
            if state["ticks"] < 240 or now - state["settled_at"] < 15:
                return
            from AuditPlayerVisibility import collect
            snapshot=frozen_snapshot(pawn)
            if snapshot!=proof["frozen_reference"]:
                stop("Frozen pose changed before "+state["ab_view"]+" capture; comparison invalid")
                return
            actual_rotation=pc.player_camera_manager.get_camera_rotation()
            expected_yaw=-55
            if abs(actual_rotation.yaw-expected_yaw)>0.1:
                stop("Camera did not reach requested yaw; comparison invalid")
                return
            camera=pawn.get_components_by_class(unreal.CameraComponent)[0]
            assert abs(camera.get_editor_property("field_of_view")-85.0)<0.0001
            proof.setdefault("views",{})[state["ab_view"]]=dict(pose=snapshot,camera_location=str(pc.player_camera_manager.get_camera_location()),camera_rotation=str(pc.player_camera_manager.get_camera_rotation()),fov=85.0,screenshot=str(SHOT))
            audit=collect(world,pawn,pc)
            from AuditAtmosphere import collect as atmosphere_audit
            atmosphere_audit(world,pc.player_camera_manager.get_camera_location(),str(OUT/("atmosphere-player-"+RUN+".json")))
            proof["runtime_audit_capture"]=audit
            from AuditPlayerVisibility import sole_clearance
            proof["sole_contact_audit"]=sole_clearance(world,pawn)
            receipt()
            visuals=[c for c in audit["pawn_components"] if c["name"] in ("RiggedSkier","LeftSki","RightSki")]
            if len(visuals)!=3 or any(not c["visible"] or c["hidden_in_game"] or c.get("owner_no_see",False) for c in visuals):
                stop("Required player visual hidden or missing; see runtime audit")
                return
            proof["settle_ticks"] = state["ticks"]
            proof["settle_seconds"] = now - state["settled_at"]
            # Specific player routes HighResShot to the GAME viewport, not the editor.
            unreal.SystemLibrary.execute_console_command(
                world, 'HighResShot 1600x900 filename="' + SHOT.as_posix() + '"', pc)
            state.update(phase="wait_file", shot_at=now, last_size=0, stable=0)
            return
        if phase == "wait_file":
            size = SHOT.stat().st_size if SHOT.exists() else 0
            state["stable"] = state["stable"] + 1 if size and size == state["last_size"] else 0
            state["last_size"] = size
            if size > 10000 and state["stable"] >= 10 and now - state["shot_at"] > 3:
                import struct
                header=SHOT.read_bytes()[:24]
                if len(header)!=24 or header[:8]!=bytes([137,80,78,71,13,10,26,10]):
                    stop("Screenshot is not a PNG")
                    return
                width,height=struct.unpack(">II",header[16:24])
                if (width,height)!=(1600,900):
                    stop("Unexpected gameplay screenshot dimensions")
                    return
                proof.update(success=False, captured=True, bytes=size,
                             png_dimensions=[width,height], requires_visual_review=True)
                # A valid image plus runtime references is NOT visual acceptance.
                # Parent must inspect Manny, BOTH curved skis and no floating blocks.
                unreal.log("FALLLINE_ACTUAL_PLAYER_CAPTURE " + str(SHOT))
                after=frozen_snapshot(pawn)
                proof["views"][state["ab_view"]]["after_pose"]=after
                if after!=proof["frozen_reference"]:
                    stop("Frozen pose changed during screenshot; comparison invalid")
                    return
                mode_index=MODES.index(state["ab_view"])
                if mode_index+1<len(MODES):
                    mode=MODES[mode_index+1]
                    diag.select(mode,state["diag_metadata"])
                    unreal.AutomationLibrary.finish_loading_before_screenshot()
                    state["ab_view"]=mode
                    globals()["SHOT"]=OUT/("player-"+mode+"-"+RUN+".png")
                    state.update(phase="render_settle",ticks=0,settled_at=now)
                    receipt()
                    return
                proof["matching_frozen_pose"]=True
                stop()
    except Exception:
        stop(traceback.format_exc())

def frame(dt):
    if state.get("in_callback"):return
    state["in_callback"]=True
    try:frame_impl(dt)
    finally:state["in_callback"]=False

receipt()
try:
    if not level.load_level("/Game/Maps/TestSlope"):
        stop("Could not load saved TestSlope")
except Exception:
    stop(traceback.format_exc())
# PIE owns its game viewport realtime. Do not remove an absent editor override.
# Installed LevelEditorSubsystem.cpp routes True to RemoveRealtimeOverride,
# which ensures if no subsystem override exists.

state["handle"] = unreal.register_slate_post_tick_callback(frame)
