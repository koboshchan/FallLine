"""Sole-owner entry after snowready. Backup required before import or mutation."""
import unreal,json,hashlib,math,datetime
from pathlib import Path
ROOT=Path("D:/FallLine")
def apply(verified_backup_receipt=None,snow_ready=False):
 assert snow_ready and verified_backup_receipt,"Parent must restore snow, exit diagnostics, take fresh full backup first"
 backup=Path(verified_backup_receipt);assert backup.is_file()
 rec=json.loads(backup.read_text());assert rec.get("verified") or rec.get("passed"),"Verified parent backup required"
 from ApplyForestEdgeStructural import snapshot
 from PopulateAlpine import _hism,_transform
 from PrepareRealDEM import height
 from ForestNoisePlan import plan
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
 oldactors=[a for a in actors.get_all_level_actors() if a.get_actor_label() in ["Healthy mature evergreen forest","Forest trunk collision"]]
 assert len(oldactors)==2,"Only approved original3200 forest cohort"
 before=snapshot()
 # Source hashes are locked by handoff receipt before imports.
 lock=json.loads((ROOT/"Saved/Logs/simple-forest-source-lock.json").read_text())
 for rel,h in lock["files"].items():
  assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
 from ImportForestFirB import import_fir_b
 from ImportForestFirC import import_fir_c
 mesh_a=unreal.load_asset("/Game/Environment/PolyHaven/fir_tree_01/SM_MatureFirA")
 meshes=[mesh_a,import_fir_b(),import_fir_c()]
 assert all(meshes)
 dims=[]
 for variant,m in zip("abc",meshes):
  b=m.get_bounding_box()
  # Explicit perasset trunk geometry receipt, not inferred from crown width.
  origin=json.loads((ROOT/("SourceAssets/PolyHaven/fir_tree_01/trunk-origin-"+variant+".json")).read_text())
  assert origin["verified"] and origin["radius_cm"]>0
  dims.append((max(b.max.x-b.min.x,b.max.y-b.min.y),b.max.z-b.min.z,b.min.z,origin["radius_cm"],origin["axis_x_cm"],origin["axis_y_cm"]))
 obstacles=[]
 for actor in actors.get_all_level_actors():
  if actor.get_actor_label() in ["Optional verge sapling","Optional edge v2 sapling"]:
   for comp in actor.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
    for i in range(comp.get_instance_count()):
     pos=comp.get_instance_transform(i,True).translation;obstacles.append((pos.x,pos.y))
 rows=plan(height,dims,obstacles=obstacles)
 # Existing juveniles and their paired trunks remain untouched.
 crowns=[];trunks=[];cylinder=unreal.load_asset("/Engine/BasicShapes/Cylinder")
 for i,m in enumerate(meshes):crowns.append(_hism(actors,m,"Organic forest "+str(i)))
 for i in range(3):trunks.append(_hism(actors,cylinder,"Organic forest trunk "+str(i),True))
 for i in range(3):
  selected=[r for r in rows if r["variant"]==i]
  crowns[i].add_instances([_transform((r["x"],r["y"],r["base_z"]),(r["scale"],)*3,r["yaw"]) for r in selected],False,True)
  trunks[i].add_instances([_transform((r["tx"],r["ty"],r["trunk_ground"]+r["trunk_height"]/2),(r["radius"]/50,r["radius"]/50,r["trunk_height"]/100),r["yaw"]) for r in selected],False,True)
  assert crowns[i].get_instance_count()==trunks[i].get_instance_count()==len(selected)
  assert crowns[i].get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
  assert trunks[i].get_collision_enabled()==unreal.CollisionEnabled.QUERY_AND_PHYSICS
  for n,r in enumerate(selected):
   ct=crowns[i].get_instance_transform(n,True);tt=trunks[i].get_instance_transform(n,True)
   cp=ct.translation;tp=tt.translation
   assert math.hypot(r["tx"]-tp.x,r["ty"]-tp.y)<.05
   assert abs(tp.z-r["trunk_height"]/2-height(tp.x,tp.y))<.05
 # Delete ONLY replaced forest actors after complete paired replacement passes.
 oldnames=[a.get_path_name() for a in oldactors]
 for a in oldactors:assert actors.destroy_actor(a)
 after=snapshot()
 # Existing nonforest snapshot fields, including136 juveniles, exact apart from approved roundoff.
 for k,v in before.items():
  if any(k.startswith(n+"/") or k.startswith(n+".") for n in oldnames):continue
  assert k in after and (after[k]==v or isinstance(v,(int,float)) and isinstance(after[k],(int,float)) and math.isclose(v,after[k],rel_tol=1e-6,abs_tol=0)),k
 out=dict(passed=True,saved=False,count=len(rows),rows=rows,backup_receipt=str(backup),variants=[m.get_path_name() for m in meshes],scope="Only original3200mature forest replaced with pairedtrunks;136juveniles unchanged; parent saves afterpass and runs ONE combinedcapture+smoke")
 (ROOT/"Saved/Logs/simple-noise-forest-runtime.json").write_text(json.dumps(out,indent=2))
 return out
