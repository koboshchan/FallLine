"""Staged source only. No launch, save, restore, export or import."""
import datetime,json,math,shutil
from pathlib import Path
import unreal
from ApplyForestEdgeStructural import snapshot,digest,packed,crown_scale_matches
from OptionalVergeDressing import _numeric_transform
from ReconcileJuvenileTrunks import distance
ROOT=Path("D:/FallLine")
PLAN=ROOT/"Saved/Logs/forest-organic-taper-offline-proposal.json"
SHA="a195fa311e9a0aa045dbb94a94759131aec07d9a00a73e54ad33a438538021fe"
OLD=ROOT/"Saved/Backups/ForestEdgeStructural-20261109-054234-087535"
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False))
def clean():
 assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
 assert not list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),"Dirty baseline"
def xf(s,cp,i):
 pre=cp+"/instances/"+str(i)+"/"
 return {k[len(pre):]:v for k,v in s.items() if k.startswith(pre)}
def inventory(plan):
 clean()
 assert digest(PLAN)==SHA
 gate=read(ROOT/"Saved/Logs/forest-organic-taper-source-gate.json")
 assert digest(Path(__file__))==gate["helper_sha256"]
 for path,h in gate["dependencies"].items():assert digest(ROOT/path)==h,path
 for path,h in plan["evidence_sha256"].items():assert digest(Path(path))==h,path
 assert plan["count"]==len(plan["rows"])==len(set(plan["ids"]))==144
 assert set(plan["ids"])=={a["index"] for a in plan["rows"]}
 old=read(OLD/"receipt.json");jm=read(OLD/"juvenile-trunk-reconciliation-manifest.json")
 final=read(ROOT/"Saved/Logs/forest-approved-apply-result.json")
 assert final["passed"] and final["saved"] and final["juvenile"]["passed"]
 assert final["juvenile"]["count"]==136 and not final["juvenile"]["existing_changes"]
 assert packed(jm["baseline"])==plan["baseline_sha256"]
 assert not set(plan["ids"]) & {a["index"] for a in old["pairs"]}
 cc={c.get_path_name():c for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() for c in a.get_components_by_class(unreal.PrimitiveComponent)}
 c=cc[plan["crown_component"]];t=cc[plan["trunk_component"]];jt=cc[final["juvenile"]["owned_component"]]
 assert c.get_instance_count()==t.get_instance_count()==3200 and jt.get_instance_count()==136
 assert c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
 for v in [t,jt]:
  assert v.get_collision_enabled()==unreal.CollisionEnabled.QUERY_AND_PHYSICS
  assert str(v.get_collision_profile_name())=="BlockAll"
  assert v.get_editor_property("static_mesh").get_path_name()=="/Engine/BasicShapes/Cylinder.Cylinder"
 for label,count in [("Optional verge sapling",120),("Optional edge v2 sapling",16)]:
  found=[v for v in cc.values() if isinstance(v,unreal.HierarchicalInstancedStaticMeshComponent) and v.get_owner().get_actor_label()==label]
  assert len(found)==1 and found[0].get_instance_count()==count
  assert found[0].get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
 baseline=snapshot();owned=final["juvenile"]["owned_actor"]
 filtered={k:v for k,v in baseline.items() if not(k.startswith(owned+"/") or k.startswith(owned+"."))}
 assert set(filtered)==set(jm["baseline"])
 for k,v in jm["baseline"].items():
  a=filtered[k]
  if "/instances/" in k and "/scale3d." in k and k.startswith(c.get_path_name()+"/"):
   assert crown_scale_matches(a,v),k
  else:assert a==v,("BASELINE",k,a,v)
 for row in final["juvenile"]["alignment"]:
  assert xf(baseline,jt.get_path_name(),row["index"])==row["actual"]
 for row in plan["rows"]:
  for name,comp,idx in [("crown",c,0),("trunk",t,1)]:
   before=row[name+"_before"];actual=xf(baseline,comp.get_path_name(),row["index"])
   assert packed(before)==row["before_sha256"][idx]
   for k,v in before.items():
    assert (crown_scale_matches(actual[k],v) if name=="crown" and k.startswith("scale3d.") else actual[k]==v)
   target=row[name+"_target"]
   assert set(target)==set(before) and all(math.isfinite(v) for v in target.values())
   assert all(target[k]==before[k] for k in before if not k.startswith("translation."))
 return baseline,c,t,jt,final

def geometry(plan,s,c,t,jt,final,targets):
 from PrepareRealDEM import height
 observed=[v["xy_cm"] for v in read(ROOT/"Saved/Logs/player-route-pass10-worldxy.json")["samples"]]
 planned=[[v["x"],v["y"]] for v in read(ROOT/"SourceAssets/DEM/manifest.json")["route"]]
 assert min(v[0] for v in planned)==-8500 and max(v[0] for v in planned)==191500
 crowns=[xf(s,c.get_path_name(),i) for i in range(3200)]
 trunks=[xf(s,t.get_path_name(),i) for i in range(3200)]
 if targets:
  for a in plan["rows"]:
   crowns[a["index"]]=a["crown_target"];trunks[a["index"]]=a["trunk_target"]
 juvenile=[v["source_transform"] for v in read(OLD/"juvenile-trunk-reconciliation-manifest.json")["rows"]]
 assert len(juvenile)==136
 for cv,tv in zip(crowns+juvenile,trunks+[a["actual"] for a in final["juvenile"]["alignment"]]):
  x=cv["translation.x"];y=cv["translation.y"]
  assert abs(tv["translation.x"]-x)<.03 and abs(tv["translation.y"]-y)<.03
  assert abs(tv["translation.z"]-tv["scale3d.z"]*50-height(x,y))<.03
 results=[]
 for a in plan["rows"]:
  i=a["index"];cv=crowns[i];tv=trunks[i];x=cv["translation.x"];y=cv["translation.y"]
  grade=math.hypot((height(x+150,y)-height(x-150,y))/300,(height(x,y+150)-height(x,y-150))/300)
  canopy=.4*cv["scale3d.z"]*1892.5411136542098
  spacing=min(math.hypot(x-v["translation.x"],y-v["translation.y"]) for n,v in enumerate(crowns+juvenile) if n!=i)
  pc=distance(x,y,planned)-canopy;oc=distance(x,y,observed)-canopy
  assert grade<=.8 and spacing>=500 and min(pc,oc)>=1300,("GEOMETRY",i,grade,spacing,pc,oc)
  assert min(distance(x,y,planned),distance(x,y,observed))-tv["scale3d.x"]*50>=650
  results.append(dict(index=i,grade=grade,spacing_cm=spacing,planned_canopy_cm=pc,observed_canopy_cm=oc))
 return results
def backup_files():
 files=[]
 for sub in ["Content/Maps","Content/Environment","Scripts","Source"]:
  directory=ROOT/sub
  if directory.exists():
   for p in directory.rglob("*"):
    assert not p.is_symlink() and not(p.stat().st_file_attributes&0x400),"No reparsepoints"
    if p.is_file() and "__pycache__" not in p.parts:files.append(p)
 for rel in ["Saved/Logs/forest-organic-taper-offline-proposal.json","Saved/Logs/forest-organic-taper-source-gate.json","Saved/Logs/forest-approved-apply-result.json","Saved/Logs/forest-edge-structural-runtime.json","Saved/Logs/juvenile-trunk-reconciliation-runtime.json","Saved/Logs/juvenile-trunk-reconciliation-manifest.json","Saved/Logs/alpine-population.json","Saved/Logs/player-route-pass10-worldxy.json","SourceAssets/DEM/manifest.json","SourceAssets/DEM/verbier.r16"]:
  files.append(ROOT/rel)
 assert any(p.name=="TestSlope.umap" for p in files)
 return sorted(set(files))
def backup_verified(baseline):
 before={str(p.relative_to(ROOT)):dict(size=p.stat().st_size,sha256=digest(p)) for p in backup_files()}
 backup=ROOT/"Saved/Backups"/("ForestOrganicTaper-"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
 assert not backup.exists()
 assert shutil.disk_usage(ROOT).free>sum(v["size"] for v in before.values())+2*1024**3
 backup.mkdir(parents=True)
 for rel,v in before.items():
  dst=backup/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dst)
  assert dst.stat().st_size==v["size"] and digest(dst)==v["sha256"]
 assert {str(p.relative_to(ROOT)) for p in backup_files()}==set(before)
 for rel,v in before.items():
  src=ROOT/rel;assert src.stat().st_size==v["size"] and digest(src)==v["sha256"]
 assert snapshot()==baseline;clean()
 receipt=dict(backup=str(backup),files=before,baseline=baseline,baseline_sha256=packed(baseline),plan_sha256=SHA,mutation_started=False,verified=True)
 write(backup/"receipt.json",receipt);assert read(backup/"receipt.json")==receipt
 (backup/"RESTORE.txt").write_text("No automatic restore. Stop without saving on failure; sole owner exits normally. Preserve original054234 and NEWpost325+136. Verify every listed SHA/size before owner-authorized filecopy/reload/nativebaseline comparison. Never delete originals.")
 return backup,receipt

def apply(snow_restored_and_previous_editor_exited=False,preflight_only=False):
 assert snow_restored_and_previous_editor_exited is True,"Parent certifies finallyrestore AND normal diagnostic exit FIRST"
 plan=read(PLAN);baseline,c,t,jt,final=inventory(plan)
 checks=geometry(plan,baseline,c,t,jt,final,True)
 updates=[]
 for row in plan["rows"]:
  items=[]
  for comp,name in [(c,"crown"),(t,"trunk")]:
   raw=comp.get_instance_transform(row["index"],True);v=row[name+"_target"]
   raw.set_editor_property("translation",unreal.Vector(v["translation.x"],v["translation.y"],v["translation.z"]))
   actual=_numeric_transform(raw);before=xf(baseline,comp.get_path_name(),row["index"])
   assert all(actual[k]==before[k] for k in before if not k.startswith("translation."))
   items.append(raw)
  updates.append((row["index"],items))
 if preflight_only:return dict(passed=True,mutation_started=False,count=144,geometry=checks)
 backup,receipt=backup_verified(baseline)
 again,cc,tt,jj,ff=inventory(plan);assert again==baseline
 geometry(plan,again,cc,tt,jj,ff,True)
 receipt["mutation_started"]=True;write(backup/"receipt.json",receipt)
 result=dict(passed=False,saved=False,backup=str(backup),plan_sha256=SHA,mutation_started=True)
 out=ROOT/"Saved/Logs/forest-organic-taper-runtime.json";write(out,result)
 try:
  for i,items in updates:
   assert c.update_instance_transform(i,items[0],True,True,True)
   assert t.update_instance_transform(i,items[1],True,True,True)
  after=snapshot();assert set(after)==set(baseline)
  allowed=set()
  for row in plan["rows"]:
   for cp in [c.get_path_name(),t.get_path_name()]:
    allowed.update(cp+"/instances/"+str(row["index"])+"/translation."+a for a in "xyz")
  unexpected=[k for k in baseline if baseline[k]!=after[k] and k not in allowed]
  moved_prefixes={cp+"/instances/"+str(row["index"])+"/" for row in plan["rows"] for cp in [c.get_path_name(),t.get_path_name()]}
  noise=[]
  for k in unexpected:
   a=baseline[k];v=after[k]
   scoped=any(k.startswith(pre) for pre in moved_prefixes) and ("/rotation." in k or "/scale3d." in k)
   finite=isinstance(a,(int,float)) and isinstance(v,(int,float)) and math.isfinite(a) and math.isfinite(v)
   limit=1e-6*max(abs(a),abs(v),1.0) if finite else 0
   noise.append(dict(key=k,before=a,after=v,delta=v-a if finite else None,limit=limit,accepted=scoped and finite and abs(v-a)<=limit))
  result["transform_roundoff"]=noise
  write(out,result)
  assert all(v["accepted"] for v in noise),("OUTSIDE SCOPE", [v for v in noise if not v["accepted"]][:20])
  for row in plan["rows"]:
   for cp,name in [(c.get_path_name(),"crown"),(t.get_path_name(),"trunk")]:
    actual=xf(after,cp,row["index"]);target=row[name+"_target"];before=xf(baseline,cp,row["index"])
    assert all(math.isfinite(actual[k]) and math.isfinite(before[k]) and abs(actual[k]-before[k])<=1e-6*max(abs(actual[k]),abs(before[k]),1.0) for k in before if not k.startswith("translation.")),"Bounded scales/rotations"
    assert all(abs(actual["translation."+a]-target["translation."+a])<.03 for a in "xyz")
  assert c.get_instance_count()==t.get_instance_count()==3200 and jt.get_instance_count()==136
  result["geometry"]=geometry(plan,after,c,t,jt,final,False)
  result.update(passed=True,count=144,post_snapshot_sha256=packed(after),save_authorized_after_all_checks=True)
  write(out,result)
  # No save API. Parent may save ONLY after passed receipt then matched pixels/smoke.
  return result
 except Exception as exc:
  result.update(error=repr(exc),save_authorized_after_all_checks=False)
  write(out,result);raise
def preflight_only(snow_restored_and_previous_editor_exited=False):
 return apply(snow_restored_and_previous_editor_exited,preflight_only=True)
