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
RESULT = OUT / ("capture-result-" + RUN + ".json")
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
state = dict(phase="startup", began=time.monotonic(), ticks=0, handle=None)
proof = dict(run=RUN, success=False, image_verified=False, screenshot=str(SHOT), mode="PIE possessed SkiPawn, paused settled pose")

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
        if now - state["began"] > 360:
            stop("Player capture timed out in " + phase)
            return
        log_path=ROOT / "Saved/Logs/player-capture.log"
        if log_path.exists():
            log_tail=log_path.read_text(errors="replace")
            if "Ensure condition failed:" in log_tail or "Fatal error:" in log_tail:
                stop("Engine ensure/fatal detected during capture; inspect dedicated capture log")
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
            # Optional pause. GameMode can reject it in PIE; no physics edits.
            requested = unreal.GameplayStatics.set_game_paused(world, True)
            paused = unreal.GameplayStatics.is_game_paused(world)
            proof.update(pause_request_return=bool(requested), paused=bool(paused))
            if not paused:
                proof["pause_note"] = "Pause refused; capture live gameplay without freezing physics"
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
            audit=collect(world,pawn,pc)
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
                stop()
    except Exception:
        stop(traceback.format_exc())

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
