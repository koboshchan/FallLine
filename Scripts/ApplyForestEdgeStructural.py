"""Approved scoped forest edge move, editor only AFTER camera AB completion.
No save, no launch. Any failed gate means stop; do not save or restore blindly.
"""
import json,math,hashlib,struct,shutil,datetime
from pathlib import Path
import unreal
from OptionalVergeDressing import _numeric_transform,_exact_diff
ROOT=Path("D:/FallLine")
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def packed(v):return hashlib.sha256(json.dumps(v,sort_keys=True,allow_nan=False).encode()).hexdigest()
def f32(v):return struct.unpack("f",struct.pack("f",v))[0]
def crown_scale_matches(actual,source):
 # User-approved relative float-noise allowance ONLY for baseline crown scales.
 return math.isfinite(actual) and math.isfinite(source) and actual>0 and source>0 and math.isclose(actual,source,rel_tol=1e-6,abs_tol=0)
def encoded(actual,source):return actual==source or actual==f32(source)
def snapshot():
 rows={}
 for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  ap=a.get_path_name();rows[ap+"/exists"]=True
  def xf(path,t):
   for k,v in _numeric_transform(t).items():rows[path+"/"+k]=v
  xf(ap+"/transform",a.get_actor_transform())
  for c in a.get_components_by_class(unreal.PrimitiveComponent):
   cp=c.get_path_name();xf(cp+"/transform",c.get_world_transform())
   rows[cp+"/collision_enabled"]=str(c.get_collision_enabled())
   rows[cp+"/collision_profile"]=str(c.get_collision_profile_name())
   if isinstance(c,unreal.StaticMeshComponent):
    mesh=c.get_editor_property("static_mesh");rows[cp+"/mesh"]=mesh.get_path_name() if mesh else None
   if isinstance(c,unreal.InstancedStaticMeshComponent):
    rows[cp+"/instance_count"]=c.get_instance_count()
    for i in range(c.get_instance_count()):xf(cp+"/instances/"+str(i),c.get_instance_transform(i,True))
 return rows
def apply(camera_ab_complete=False,preflight_only=False):
 assert camera_ab_complete is True,"Sole owner must certify camera A/B completed"
 assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None,"EDITOR NON PIE ONLY"
 dirty=list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())
 assert not dirty,"Quiescent saved baseline required BEFORE backup; owner saves intentional preexisting changes separately, never auto-save here"
 from PopulateAlpine import _transform
 planpath=ROOT/"Saved/Logs/forest-edge-structural-plan.json"
 plan=json.loads(planpath.read_text())
 assert digest(ROOT/"Saved/Logs/alpine-population.json")==plan["baseline_manifest_sha256"]
 for p,h in plan["planned_sources"].items():assert digest(Path(p))==h,p
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
 def unique(label):
  aa=[a for a in actors if a.get_actor_label()==label];assert len(aa)==1,label
  cc=aa[0].get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent);assert len(cc)==1
  return cc[0]
 crowns=unique("Healthy mature evergreen forest");trunks=unique("Forest trunk collision")
 assert crowns.get_instance_count()==trunks.get_instance_count()==3200
 assert crowns.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
 assert str(trunks.get_collision_profile_name())=="BlockAll"
 assert trunks.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION
 assert trunks.get_editor_property("static_mesh").get_path_name()=="/Engine/BasicShapes/Cylinder.Cylinder"
 bb=crowns.get_editor_property("static_mesh").get_bounding_box();meshheight=bb.max.z-bb.min.z
 baseline=snapshot();pairs=[];updates=[];scale_audit=[]
 for row in plan["rows"]:
  i=row["index"];o=row["original"];n=row["proposed"]
  assert packed(o)==row["original_sha256"]
  oldc=crowns.get_instance_transform(i,True);oldt=trunks.get_instance_transform(i,True)
  cv=_numeric_transform(oldc);tv=_numeric_transform(oldt)
  for v in [cv,tv]:
   assert encoded(v["translation.x"],o["x"]) and encoded(v["translation.y"],o["y"]),("PAIR XY",i,v)
  s=o["height_cm"]/meshheight;th=min(o["height_cm"]*.7,1300)
  assert encoded(cv["translation.z"],o["z"]-bb.min.z*s-12),("CROWN Z",i)
  assert encoded(tv["translation.z"],o["z"]+th/2),("TRUNK Z",i)
  scaleproof=dict(index=i,source_height_cm=o["height_cm"],current_mesh_height_cm=meshheight,current_mesh_min_z=bb.min.z,current_mesh_max_z=bb.max.z,source_formula_scale=s,source_formula_scale_f32=f32(s),actual_crown=cv,actual_trunk=tv,actual_mesh=crowns.get_editor_property("static_mesh").get_path_name(),component_transform=_numeric_transform(crowns.get_world_transform()),source_manifest_sha256=plan["baseline_manifest_sha256"],differences={axis:dict(actual=cv["scale3d."+axis],expected=s,expected_f32=f32(s),minus_source=cv["scale3d."+axis]-s,minus_f32=cv["scale3d."+axis]-f32(s)) for axis in "xyz"})
  if not all(encoded(cv["scale3d."+axis],s) for axis in "xyz"):
   Path("D:/FallLine/Saved/Logs/forest-native-scale-failure.json").write_text(json.dumps(scaleproof,indent=2,allow_nan=False))
  scale_audit.append(dict(index=i,axes={axis:dict(actual=cv["scale3d."+axis],expected=s,ulp_error=(cv["scale3d."+axis]-s)/math.ulp(s),passed=crown_scale_matches(cv["scale3d."+axis],s)) for axis in "xyz"}))
  for axis,value in zip("xyz",[o["trunk_radius_cm"]/50,o["trunk_radius_cm"]/50,th/100]):
   assert encoded(tv["scale3d."+axis],value),("TRUNK SCALE",i,axis)
  assert all(tv["rotation."+a]==v for a,v in zip("xyzw",[0.,0.,0.,1.])),("TRUNK ROT",i)
  sc=n["height_cm"]/meshheight
  newc=_transform((n["x"],n["y"],n["z"]-bb.min.z*sc-12),(sc*n["width"],sc*n["width"],sc),n["yaw"])
  newt=_transform((n["x"],n["y"],n["z"]+n["trunk_height_cm"]/2),(n["trunk_radius_cm"]/50,n["trunk_radius_cm"]/50,n["trunk_height_cm"]/100),n["yaw"])
  pair=dict(index=i,crown_component=crowns.get_path_name(),trunk_component=trunks.get_path_name(),crown_before=cv,trunk_before=tv,crown_before_sha256=packed(cv),trunk_before_sha256=packed(tv),crown_target=_numeric_transform(newc),trunk_target=_numeric_transform(newt),source=row)
  pairs.append(pair);updates.append((i,newc,newt))
 Path("D:/FallLine/Saved/Logs/forest-crown-scale-all325.json").write_text(json.dumps(dict(count=len(scale_audit),rows=scale_audit),indent=2,allow_nan=False))
 assert len(scale_audit)==325 and all(a["passed"] for row in scale_audit for a in row["axes"].values()),"CROWN SCALE beyond relative tolerance 1e-6; see forest-crown-scale-all325.json; STOP"
 if preflight_only:
  return dict(preflight_only=True,passed_preflight=True,mutation_started=False,pairs=pairs)
 # Quiescent backup BEFORE first update, including map/generated assets/source/manifests.
 stamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
 backup=ROOT/"Saved/Backups"/("ForestEdgeStructural-"+stamp);backup.mkdir(parents=True)
 files=[]
 for sub in ["Content/Maps","Content/Environment","Scripts","Source"]:
  directory=ROOT/sub
  if directory.exists():files.extend(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
 files.extend([ROOT/"Saved/Logs/alpine-population.json",planpath,ROOT/"SourceAssets/DEM/manifest.json",ROOT/"Saved/Logs/player-route-pass10-worldxy.json"])
 assert any(p.name=="TestSlope.umap" for p in files),"No baseline map"
 copied=[]
 for src in sorted(set(files)):
  rel=src.relative_to(ROOT);before=(src.stat().st_size,digest(src))
  dst=backup/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  assert (src.stat().st_size,digest(src))==before==(dst.stat().st_size,digest(dst)),"Backup changed"
  copied.append(dict(relative=str(rel),size=before[0],sha256=before[1]))
 for item in copied:
  src=ROOT/item["relative"];assert src.stat().st_size==item["size"] and digest(src)==item["sha256"]
 assert snapshot()==baseline,"Scene changed during backup"
 receipt=dict(backup=str(backup),files=copied,pairs=pairs,baseline=baseline,baseline_sha256=packed(baseline),plan_sha256=digest(planpath),mutation_started=False)
 (backup/"receipt.json").write_text(json.dumps(receipt,indent=2,allow_nan=False))
 (backup/"RESTORE.txt").write_text("Stop without saving on any failure. Sole owner exits editor normally WITHOUT save. Verify every backup SHA/size against receipt.json. Preserve failed map separately if already saved; do not overwrite diagnostics. With editor closed restore exactly listed relative files by copy, not delete. Verify restored bytes SHA/size. Reload baseline map and compare exact snapshot to receipt baseline before further work. No automatic blind restore.")
 receipt["mutation_started"]=True
 (backup/"receipt.json").write_text(json.dumps(receipt,indent=2,allow_nan=False))
 for i,c,t in updates:
  assert crowns.update_instance_transform(i,c,True,True,True)
  assert trunks.update_instance_transform(i,t,True,True,True)
 after=snapshot();differences=_exact_diff(baseline,after)
 allowed=set()
 for pair in pairs:
  i=pair["index"]
  for cp in [pair["crown_component"],pair["trunk_component"]]:
   prefix=cp+"/instances/"+str(i)+"/"
   allowed.update(prefix+k for k in pair["crown_before"])
 unexpected=[d for d in differences if d["path"] not in allowed]
 result=dict(backup=str(backup),moved_pairs=len(pairs),unexpected_changes=unexpected,all_changes=differences,tree_count=crowns.get_instance_count(),trunk_count=trunks.get_instance_count(),pair_alignment=[])
 path=ROOT/"Saved/Logs/forest-edge-structural-runtime.json"
 path.write_text(json.dumps(result,indent=2,allow_nan=False))
 assert not unexpected,"OUTSIDE SCOPE CHANGE DO NOT SAVE"
 for pair in pairs:
  i=pair["index"];n=pair["source"]["proposed"]
  cv=_numeric_transform(crowns.get_instance_transform(i,True));tv=_numeric_transform(trunks.get_instance_transform(i,True))
  # Explicit native float32 storage verification for changed targets only.
  # Unchanged fields above retain EXACT full precision equality, no tolerances.
  for actual,target in [(cv,pair["crown_target"]),(tv,pair["trunk_target"])]:
   # q and -q encode exactly the same orientation. Match the whole quaternion,
   # never individual signs, before the unchanged target-error checks.
   actual=dict(actual)
   qkeys=["rotation."+a for a in "xyzw"]
   if sum(actual[k]*target[k] for k in qkeys)<0:
    for k in qkeys:actual[k]=-actual[k]
   for field,value in target.items():
    limit=.03 if field.startswith("translation.") else .000002
    assert abs(actual[field]-value)<=limit,("TARGET",i,field,actual[field],value)
  assert cv["translation.x"]==tv["translation.x"] and cv["translation.y"]==tv["translation.y"]
  actualheight=tv["scale3d.z"]*100;actualradius=tv["scale3d.x"]*50
  bottom=tv["translation.z"]-actualheight/2
  assert abs(bottom-n["z"])<.03 and abs(actualheight-n["trunk_height_cm"])<.03 and abs(actualradius-n["trunk_radius_cm"])<.003
  result["pair_alignment"].append(dict(index=i,trunk_bottom_error_cm=bottom-n["z"],trunk_height_cm=actualheight,trunk_radius_cm=actualradius,crown=cv,trunk=tv))
 assert crowns.get_instance_count()==trunks.get_instance_count()==3200
 assert str(trunks.get_collision_profile_name())=="BlockAll" and trunks.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION
 result["passed"]=True
 path.write_text(json.dumps(result,indent=2,allow_nan=False))
 unreal.log("FALLLINE_FOREST_EDGE_STRUCTURAL "+json.dumps(dict(passed=True,pairs=len(pairs),backup=str(backup))))
 return result

def preflight_only():
 """Guaranteed read-only: return or raise before backup, copying or scene mutation."""
 return apply(camera_ab_complete=True,preflight_only=True)
