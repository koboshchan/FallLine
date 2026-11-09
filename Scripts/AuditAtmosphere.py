"""Read-only PIE/editor atmosphere proof. No actor/renderer/physics mutation.
Call collect(world, camera_location, output_path) just before the actual screenshot.
Installed UE5.8 SkyAtmosphereComponent.h uses km for bottom_radius;
SceneComponent positions and DEM/camera positions use cm.
"""
import unreal,json,math
from pathlib import Path

def collect(world,camera_location,output_path):
    dem=json.loads(Path("D:/FallLine/SourceAssets/DEM/manifest.json").read_text())
    low,high=map(float,dem["world_height_range_cm"])
    camera=[float(camera_location.x),float(camera_location.y),float(camera_location.z)]
    report=dict(world=world.get_path_name(),camera_cm=camera,dem_height_range_cm=[low,high],
                dem_extent_cm=dem["bounds_cm"],sky=[],fog=[],exposure=[])
    def component(c):
        return dict(path=c.get_path_name(),visible=c.is_visible(),
                    hidden_in_game=c.get_editor_property("hidden_in_game"),
                    location_cm=[float(v) for v in c.get_world_location().to_tuple()])
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
        for c in actor.get_components_by_class(unreal.SkyAtmosphereComponent):
            d=component(c)
            for key in ["transform_mode","bottom_radius","atmosphere_height",
                        "aerial_pespective_view_distance_scale","mie_scattering_scale",
                        "rayleigh_scattering_scale"]:
                value=c.get_editor_property(key)
                d[key]=str(value) if key=="transform_mode" else value
            mode=c.get_editor_property("transform_mode")
            radius=float(d["bottom_radius"])*100000.0
            if mode==unreal.SkyAtmosphereTransformMode.PLANET_TOP_AT_ABSOLUTE_WORLD_ORIGIN:
                center=[0,0,-radius];ground=0.0
            elif mode==unreal.SkyAtmosphereTransformMode.PLANET_TOP_AT_COMPONENT_TRANSFORM:
                ground=d["location_cm"][2]
                center=[d["location_cm"][0],d["location_cm"][1],ground-radius]
            else:
                center=d["location_cm"];ground=center[2]+radius
            d["planet_top_z_cm"]=ground
            d["camera_radial_altitude_cm"]=math.sqrt(sum((a-b)**2 for a,b in zip(camera,center)))-radius
            d["lowest_dem_above_planet_top_cm"]=low-ground
            d["valid_above_ground"]=d["camera_radial_altitude_cm"]>0 and low>ground
            report["sky"].append(d)
        for c in actor.get_components_by_class(unreal.ExponentialHeightFogComponent):
            d=component(c)
            for key in ["fog_density","fog_height_falloff","start_distance","fog_max_opacity",
                        "enable_volumetric_fog","volumetric_fog_distance","volumetric_fog_start_distance"]:
                d[key]=c.get_editor_property(key)
            d["camera_above_fog_origin_cm"]=camera[2]-d["location_cm"][2]
            report["fog"].append(d)
        for c in actor.get_components_by_class(unreal.PostProcessComponent):
            d=component(c)
            settings=c.get_editor_property("settings")
            for key in ["auto_exposure_min_brightness","auto_exposure_max_brightness","auto_exposure_bias"]:
                d[key]=settings.get_editor_property(key)
            report["exposure"].append(d)
    report["structural_pass"]=bool(report["sky"] and report["fog"]) and all(
        s["valid_above_ground"] and s["visible"] and not s["hidden_in_game"] for s in report["sky"])
    report["image_verified"]=False
    Path(output_path).write_text(json.dumps(report,indent=2))
    unreal.log("FALLLINE_ATMOSPHERE_AUDIT "+json.dumps(report))
    return report
