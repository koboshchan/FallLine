"""Sampler-only deterministic Swiss alpine ecosystem, HISM render/collision batches.
Contract surface_sampler(x_cm,y_cm)->world_z_cm, bounds=(xmin,ymin,xmax,ymax).
Never derives independent terrain coordinates, units or elevation offsets.
"""
import unreal,math,random,json
from pathlib import Path
def _hism(actors,mesh,label,collision=False):
    owner=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,0),unreal.Rotator())
    owner.set_actor_label(label)
    owner.static_mesh_component.set_collision_profile_name('NoCollision')
    sub=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles=sub.k2_gather_subobject_data_for_instance(owner)
    assert handles,"No subobject handles for "+label
    params=unreal.AddNewSubobjectParams(parent_handle=handles[0],new_class=unreal.HierarchicalInstancedStaticMeshComponent)
    handle,reason=sub.add_new_subobject(params)
    data=sub.k2_find_subobject_data_from_handle(handle)
    assert data,"HISM creation failed "+str(reason)
    comp=unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data,False)
    assert isinstance(comp,unreal.HierarchicalInstancedStaticMeshComponent),str(reason)
    comp.set_static_mesh(mesh)
    comp.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    if collision:comp.set_visibility(False)
    return comp
def _transform(pos,scale,yaw=0):
    return unreal.Transform(location=unreal.Vector(*pos),rotation=unreal.Rotator(pitch=0,yaw=yaw,roll=0),scale=unreal.Vector(*scale))
def atmosphere(actors):
    """Tune existing TestSlope components, no duplicate sky or sun."""
    # Only the atmosphere component moves. DEM stays in its certified world frame.
    # Engine sky lengths are km, scene component positions are cm.
    dem=json.loads(Path("D:/FallLine/SourceAssets/DEM/manifest.json").read_text())
    ground_z=float(dem["world_height_range_cm"][0])-10000.0
    counts={}
    for actor in actors.get_all_level_actors():
        for c in actor.get_components_by_class(unreal.ExponentialHeightFogComponent):
            c.set_fog_density(.018)
            # Broad altitude transition, not a narrow blue wall across the valley.
            c.set_fog_height_falloff(.035)
            c.set_start_distance(4500)
            c.set_fog_max_opacity(.88)
            c.set_directional_inscattering_exponent(8)
            c.set_directional_inscattering_start_distance(18000)
            c.set_directional_inscattering_color(unreal.LinearColor(.92,.78,.61,1))
            c.set_fog_inscattering_color(unreal.LinearColor(.60,.66,.72,1))
            c.set_volumetric_fog(True)
            c.set_volumetric_fog_distance(400000)
            c.set_volumetric_fog_start_distance(2500)
            counts["fog"]=counts.get("fog",0)+1
        for c in actor.get_components_by_class(unreal.DirectionalLightComponent):
            c.set_editor_property("relative_rotation",unreal.Rotator(pitch=-18,yaw=-42,roll=0))
            c.set_intensity(45000.0)
            c.set_light_source_angle(.65)
            c.set_atmosphere_sun_light(True)
            c.set_light_color(unreal.LinearColor(1,.91,.78,1))
            counts["sun"]=counts.get("sun",0)+1
        for c in actor.get_components_by_class(unreal.SkyAtmosphereComponent):
            c.set_editor_property("transform_mode",unreal.SkyAtmosphereTransformMode.PLANET_TOP_AT_COMPONENT_TRANSFORM)
            c.set_world_location(unreal.Vector(0,0,ground_z),False,True)
            # Preserve the Earth ground radius default (6360 kilometres).
            assert c.get_editor_property("bottom_radius") > 1000
            c.set_rayleigh_scattering_scale(.85)
            c.set_mie_scattering_scale(1.8)
            c.set_mie_anisotropy(.72)
            # Spelling "pespective" matches installed SkyAtmosphereComponent.h.
            c.set_aerial_pespective_view_distance_scale(2.5)
            counts["sky"]=counts.get("sky",0)+1
    unreal.log("FALLLINE_ALPINE_ATMOSPHERE "+json.dumps(counts))
    return counts
def populate(pine,rock,surface_sampler=None,bounds=None):
    assert callable(surface_sampler),"DEM dependency gate: supplied height sampler required"
    assert bounds is not None and len(bounds)==4,"DEM dependency gate: world-cm bounds required"
    xmin,ymin,xmax,ymax=map(float,bounds)
    assert xmin<xmax and ymin<ymax,"Bounds order must be xmin,ymin,xmax,ymax"
    def sample(x,y):
        if not (xmin<=x<=xmax and ymin<=y<=ymax):
            return None
        z=float(surface_sampler(x,y))
        return z if math.isfinite(z) else None
    from ImportMatureFir import import_fir
    pine=import_fir()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rng=random.Random(14821)
    cylinder=unreal.load_asset('/Engine/BasicShapes/Cylinder')
    sphere=unreal.load_asset('/Engine/BasicShapes/Sphere')
    assert cylinder and sphere and pine and rock
    def size(mesh):
        b=mesh.get_bounding_box()
        return b.min,b.max,(b.max.x-b.min.x,b.max.y-b.min.y,b.max.z-b.min.z)
    pmin,pmax,psize=size(pine);rmin,rmax,rsize=size(rock)
    assert psize[2]>0 and rsize[2]>0
    crowns=_hism(actors,pine,"Healthy mature evergreen forest")
    trunks=_hism(actors,cylinder,"Forest trunk collision",True)
    rocks=_hism(actors,rock,"Exposed granite outcrops")
    solids=_hism(actors,sphere,"Granite collision",True)
    crown_xf=[];trunk_xf=[];rock_xf=[];solid_xf=[]
    report={"seed":14821,"sampler":"supplied world-cm callable","bounds":list(bounds),"pines":[],"rocks":[],"collision":"HISM BlockAll trunks and inset boulders; crowns NoCollision"}
    occupied=set()
    xlo=max(xmin+500,-40000);xhi=min(xmax-500,200000)
    ylo=max(ymin+500,-70000);yhi=min(ymax-500,70000)
    assert xlo<xhi and ylo<yhi
    for i in range(15000):
        # Dense visible near-camera groves first, broader irregular forest beyond.
        if i<3000:
            x=rng.uniform(max(xlo,-20000),min(xhi,42000))
            y=rng.choice([-1,1])*rng.uniform(4700,min(28000,yhi,-ylo))
        else:
            x=rng.uniform(xlo,xhi);y=rng.uniform(ylo,yhi)
        if abs(y)<4500:continue
        cell=(int(x//850),int(y//850))
        if cell in occupied:continue
        z=sample(x,y)
        if z is None or sample(x+150,y) is None or sample(x-150,y) is None or sample(x,y+150) is None or sample(x,y-150) is None:continue
        dx=(surface_sampler(x+150,y)-surface_sampler(x-150,y))/300
        dy=(surface_sampler(x,y+150)-surface_sampler(x,y-150))/300
        if not math.isfinite(z) or math.hypot(dx,dy)>.85:continue
        # Altitude relative to the supplied spawn ground, never a new terrain offset.
        if z>surface_sampler(-8500,0)+32000:continue
        occupied.add(cell)
        target=rng.uniform(1100,2250)
        s=target/psize[2];yaw=rng.uniform(0,360)
        # Single tree derivative is origin-centred at its trunk.
        crown_xf.append(_transform((x,y,z-pmin.z*s-12),(s,s,s),yaw))
        trunk_h=min(target*.70,1300);radius=rng.uniform(17,32)
        trunk_xf.append(_transform((x,y,z+trunk_h/2),(radius/50,radius/50,trunk_h/100)))
        report["pines"].append({"x":x,"y":y,"z":z,"height_cm":target,"trunk_radius_cm":radius})
        if len(crown_xf)>=3200:break
    for i in range(420):
        x=rng.uniform(xlo,xhi);y=rng.uniform(ylo,yhi)
        if abs(y)<4300:continue
        z=sample(x,y)
        if z is None:continue
        target=rng.uniform(180,850)
        s=target/rsize[2];yaw=rng.uniform(0,360)
        center=((rmin.x+rmax.x)*.5*s,(rmin.y+rmax.y)*.5*s)
        c,sn=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
        cx=x+center[0]*c-center[1]*sn;cy=y+center[0]*sn+center[1]*c
        base=z-rmin.z*s-target*.25
        rock_xf.append(_transform((x,y,base),(s,s,s),yaw))
        solid_xf.append(_transform((cx,cy,base+(rmin.z+rmax.z)*.5*s),(rsize[0]*s*.82/100,rsize[1]*s*.82/100,target*.82/100),yaw))
        report["rocks"].append({"x":x,"y":y,"z":z,"height_cm":target})
    assert len(crown_xf)>400,"Too few suitable forest sites; inspect DEM alignment"
    for comp,transforms in [(crowns,crown_xf),(trunks,trunk_xf),(rocks,rock_xf),(solids,solid_xf)]:
        comp.add_instances(transforms,False,True)
        assert comp.get_instance_count()==len(transforms)
    report["atmosphere"]=atmosphere(actors)
    report["counts"]={"pines":len(crown_xf),"rocks":len(rock_xf),"hism_components":4}
    Path('D:/FallLine/Saved/Logs/alpine-population.json').write_text(json.dumps(report,indent=2))
    unreal.log("FALLLINE_ALPINE_POPULATED "+json.dumps(report["counts"]))
    return report
