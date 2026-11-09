"""Capture the actual PIE pawn through its possessed player viewport.
Runtime-only camera framing and paused pose, no saved level or physics edits.
Requires interactive UnrealEditor.exe, not -game/-nullrhi or a commandlet.
"""
import unreal, time, json, traceback
from pathlib import Path

ROOT = Path("D:/FallLine")
OUT = ROOT / "Saved/Screenshots/ActualPlayer"
OUT.mkdir(parents=True, exist_ok=True)
RUN = str(time.time_ns())
SHOT = OUT / ("player-" + RUN + ".png")
RESULT = OUT / "capture-result.json"
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
state = dict(phase="startup", began=time.monotonic(), ticks=0, handle=None)
proof = dict(run=RUN, success=False, screenshot=str(SHOT), mode="PIE possessed SkiPawn, paused settled pose")

def receipt():
    RESULT.write_text(json.dumps(proof, indent=2), encoding="utf-8")

def stop(error=None):
    if error:
        proof["error"] = error
        unreal.log_error(error)
    receipt()
    # End PIE asynchronously. Release keepalive only after its world is gone.
    state["phase"] = "ending"
    state["end_at"] = time.monotonic()
    level.editor_request_end_play()

def frame(dt):
    try:
        now = time.monotonic()
        phase = state["phase"]
        if phase == "ending":
            if editor.get_game_world() is None:
                unreal.unregister_slate_post_tick_callback(state["handle"])
                unreal.EditorPythonScripting.set_keep_python_script_alive(False)
            elif now - state["end_at"] > 45:
                proof["error"] = "PIE did not end normally within 45 seconds"
                proof["success"] = False
                receipt()
                unreal.unregister_slate_post_tick_callback(state["handle"])
                unreal.EditorPythonScripting.set_keep_python_script_alive(False)
            return
        if now - state["began"] > 360:
            stop("Player capture timed out in " + phase)
            return
        if phase == "startup":
            if now - state["began"] < 3:
                return
            level.editor_request_begin_play()
            state["phase"] = "wait_pawn"
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
                         initial_dem_clearance_cm=clearance)
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
            # Runtime camera only. Rear three-quarter angle includes both skis.
            boom = pawn.get_components_by_class(unreal.SpringArmComponent)[0]
            boom.set_editor_property("target_arm_length", 520.0)
            boom.set_editor_property("enable_camera_lag", False)
            pc.set_control_rotation(unreal.Rotator(pitch=-12, yaw=-24, roll=0))
            unreal.SystemLibrary.execute_console_command(world, "r.MotionBlurQuality 0", pc)
            state["pose_at"] = now
            state["phase"] = "settle_pose"
            return
        if phase == "settle_pose":
            if now - state["pose_at"] < 1.0:
                return
            if not unreal.GameplayStatics.set_game_paused(world, True):
                stop("Could not pause settled player pose")
                return
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
                proof.update(success=True, bytes=size)
                unreal.log("FALLLINE_ACTUAL_PLAYER_CAPTURE " + str(SHOT))
                stop()
    except Exception:
        stop(traceback.format_exc())

receipt()
if not level.load_level("/Game/Maps/TestSlope"):
    raise RuntimeError("Could not load saved TestSlope")
level.editor_set_viewport_realtime(True)
state["handle"] = unreal.register_slate_post_tick_callback(frame)
