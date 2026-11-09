"""Future capture diagnostics only. Import manually after current capture ends.
Read-only world inspection, no level/component/camera mutations.
"""
import unreal
def collect(world,pawn,pc):
    def component(c):
        parent=c.get_attach_parent()
        row=dict(name=c.get_name(),type=c.get_class().get_name(),
                 parent=parent.get_name() if parent else None,
                 visible=c.is_visible(),
                 hidden_in_game=c.get_editor_property("hidden_in_game"),
                 location=str(c.get_world_location()),
                 scale=str(c.get_world_scale()))
        if isinstance(c,unreal.PrimitiveComponent):
            row.update(owner_no_see=c.get_editor_property("owner_no_see"),
                       only_owner_see=c.get_editor_property("only_owner_see"))
        if isinstance(c,unreal.StaticMeshComponent):
            mesh=c.get_editor_property("static_mesh")
            row["asset"]=mesh.get_path_name() if mesh else None
        if isinstance(c,unreal.PoseableMeshComponent):
            mesh=c.get_skinned_asset()
            row["asset"]=mesh.get_path_name() if mesh else None
        return row
    camera=pc.get_editor_property("player_camera_manager")
    rows=dict(pawn=pawn.get_path_name(),
              pawn_scale=str(pawn.get_actor_scale3d()),
              pawn_components=[component(c) for c in pawn.get_components_by_class(unreal.SceneComponent)],
              camera_location=str(camera.get_camera_location()),
              camera_rotation=str(camera.get_camera_rotation()))
    rows["test_slope_visuals"]=[]
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,"/Script/FallLine.TestSlope")):
        rows["test_slope_visuals"].append(dict(actor=actor.get_path_name(),
            components=[component(c) for c in actor.get_components_by_class(unreal.StaticMeshComponent)]))
    return rows

def sole_clearance(world,pawn):
    """Original OBJ graphite-base vertices transformed by actual ski components.
    Read-only contact evidence, never infer contact from pawn origin.
    """
    from pathlib import Path
    import hashlib
    from PrepareRealDEM import height
    path=Path("D:/FallLine/SourceAssets/Skis/ski.obj")
    data=path.read_bytes()
    vertices=[];indices=set();material=None
    for line in data.decode().splitlines():
        if line.startswith("v "): vertices.append(tuple(map(float,line.split()[1:4])))
        elif line.startswith("usemtl "): material=line[7:]
        elif line.startswith("f ") and material=="GraphiteBase":
            indices.update(int(x.split("/")[0])-1 for x in line.split()[1:])
    # GraphiteBase also includes binding boxes. Sole is the first 388 strip vertices.
    indices=sorted(i for i in indices if i<388)
    if not indices: raise RuntimeError("No original sole vertices")
    result=dict(origin_clearance_cm=None,source_obj_sha256=hashlib.sha256(data).hexdigest(),
                vertex_basis="Original OBJ base strip, importer convert_scene=False; NOT GPU readback",
                skis=[])
    origin=pawn.get_actor_location()
    result["origin_clearance_cm"]=origin.z-height(origin.x,origin.y)
    for c in pawn.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() not in ("LeftSki","RightSki"): continue
        transform=c.get_world_transform()
        points=[transform.transform_location(unreal.Vector(*vertices[i])) for i in indices]
        samples=[]
        for point in points:
            dz=point.z-height(point.x,point.y)
            samples.append(dict(x=point.x,y=point.y,z=point.z,dem_clearance_cm=dz))
        lowest=min(samples,key=lambda a:a["z"])
        # Trace ski extremes and lowest world vertex, ignoring player's own collision.
        tracepoints=[min(samples,key=lambda a:a["x"]),max(samples,key=lambda a:a["x"]),lowest]
        traces=[]
        for q in tracepoints:
            z=height(q["x"],q["y"])
            hit=unreal.SystemLibrary.line_trace_single(world,
                unreal.Vector(q["x"],q["y"],z+500),
                unreal.Vector(q["x"],q["y"],z-500),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],
                unreal.DrawDebugTrace.NONE,True)
            if hit is None: raise RuntimeError("No terrain collision under ski sole")
            point=hit.to_tuple()[5]
            traces.append(dict(sole=q,terrain_impact=str(point),
                               clearance_cm=q["z"]-point.z))
        # Generator curved_lift explicitly begins the upturns outside [-72,61].
        # Preserve full sole measurements above; this is the main cambered bearing strip.
        bearing=[]
        for i in indices:
            local=vertices[i]
            if not -72.0 <= local[0] <= 61.0: continue
            q=transform.transform_location(unreal.Vector(*local))
            z=height(q.x,q.y)
            hit=unreal.SystemLibrary.line_trace_single(world,
                unreal.Vector(q.x,q.y,z+500),unreal.Vector(q.x,q.y,z-500),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[pawn],
                unreal.DrawDebugTrace.NONE,True)
            if hit is None: raise RuntimeError("Missing bearing-region terrain collision")
            impact=hit.to_tuple()[5]
            bearing.append(dict(source_vertex=i,local_xyz=local,world_xyz=[q.x,q.y,q.z],
                terrain_impact_xyz=[impact.x,impact.y,impact.z],
                dem_clearance_cm=q.z-z,collision_clearance_cm=q.z-impact.z))
        if len(bearing)!=134: raise RuntimeError("Bearing geometry provenance changed")
        def stats(key):
            a=sorted(row[key] for row in bearing)
            return dict(minimum=min(a),maximum=max(a),mean=sum(a)/len(a),
                        median=(a[len(a)//2-1]+a[len(a)//2])/2)
        result.setdefault("bearing_regions",[]).append(dict(ski=c.get_name(),
            provenance="GenerateSkiGeometry.curved_lift: Front above61cm Tail below-72cm; main sole retains camber",
            count=len(bearing),local_x_range_cm=[-72,61],samples=bearing,
            dem_stats=stats("dem_clearance_cm"),collision_stats=stats("collision_clearance_cm")))
        result["skis"].append(dict(name=c.get_name(),world_transform=str(transform),
            lowest_world_vertex=lowest,min_dem_clearance_cm=min(q["dem_clearance_cm"] for q in samples),
            max_dem_clearance_cm=max(q["dem_clearance_cm"] for q in samples),
            sole_vertex_count=len(samples),terrain_collision_traces=traces))
    if len(result["skis"])!=2: raise RuntimeError("Both ski sole proofs required")
    return result
