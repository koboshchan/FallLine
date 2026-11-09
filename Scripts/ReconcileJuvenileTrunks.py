"""Separate explicitly authorized juvenile trunk reconciliation, AFTER 325 gate."""
import json,math,hashlib
from pathlib import Path
import unreal
from ApplyForestEdgeStructural import snapshot,digest
from OptionalVergeDressing import _numeric_transform,_exact_diff
ROOT=Path("D:/FallLine")
LABELS={"Optional verge sapling":120,"Optional edge v2 sapling":16}
def distance(x,y,points):
 best=float("inf")
 for a,b in zip(points,points[1:]):
  vx,vy=b[0]-a[0],b[1]-a[1];l=vx*vx+vy*vy
  assert l>0
  u=max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/l))
  best=min(best,math.hypot(x-a[0]-u*vx,y-a[1]-u*vy))
 return best
def dimensions(transform,mesh_box):
 height=(mesh_box.max.z-mesh_box.min.z)*transform["scale3d.z"]
 assert height>0
 # Same 70% capped trunk-height model, proportional 24.5cm / mature18.925m reference radius.
 width=math.sqrt(transform["scale3d.x"]*transform["scale3d.y"])/transform["scale3d.z"]
 radius=max(2.,min(16.,24.5*height/1892.54074*width))
 return height,min(height*.70,1300.),radius
def apply():
 from PopulateAlpine import _hism,_transform
 assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None
 previous=json.loads((ROOT/"Saved/Logs/forest-edge-structural-runtime.json").read_text())
 assert previous.get("passed") and previous["moved_pairs"]==325,"325 phase must pass FIRST"
 backup=Path(previous["backup"]);assert (backup/"receipt.json").exists()
 assert digest(ROOT/"Scripts/ReconcileJuvenileTrunks.py")==json.loads((ROOT/"Saved/Logs/juvenile-trunk-source-gate.json").read_text())["helper_sha256"]
 sub=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=sub.get_all_level_actors()
 assert not any(a.get_actor_label()=="Reconciled juvenile fir trunks" for a in actors),"No duplicate phase"
 observed=[s["xy_cm"] for s in json.loads((ROOT/"Saved/Logs/player-route-pass10-worldxy.json").read_text())["samples"]]
 planned=[[r["x"],r["y"]] for r in json.loads((ROOT/"SourceAssets/DEM/manifest.json").read_text())["route"]]
 rows=[];blocked=[];transforms=[]
 from PrepareRealDEM import height as ground
 for label,count in LABELS.items():
  found=[a for a in actors if a.get_actor_label()==label];assert len(found)==1,("Exact juvenile inventory mismatch",label,len(found))
  cc=found[0].get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent);assert len(cc)==1
  c=cc[0];assert c.get_instance_count()==count
  assert c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
  mesh=c.get_editor_property("static_mesh");assert "Fir" in mesh.get_name() or "fir" in mesh.get_name()
  box=mesh.get_bounding_box()
  for i in range(count):
   raw=c.get_instance_transform(i,True);v=_numeric_transform(raw)
   assert all(v["scale3d."+a]>0 for a in "xyz")
   assert abs(v["rotation.x"])<.000002 and abs(v["rotation.y"])<.000002,"Unexpected tilt: need oriented trunk derivation"
   h,th,r=dimensions(v,box);x=v["translation.x"];y=v["translation.y"];z=ground(x,y)
   canopy=h*.40*max(v["scale3d.x"],v["scale3d.y"])/v["scale3d.z"]
   pc=distance(x,y,planned)-r;oc=distance(x,y,observed)-r
   row=dict(source_actor=found[0].get_path_name(),source_component=c.get_path_name(),instance_index=i,source_transform=v,source_transform_sha256=hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest(),source_mesh=mesh.get_path_name(),world_ground_z=z,height_cm=h,trunk_height_cm=th,trunk_radius_cm=r,planned_trunk_clearance_cm=pc,observed_trunk_clearance_cm=oc,planned_canopy_clearance_cm=distance(x,y,planned)-canopy,new_trunk_instance=len(rows))
   if min(pc,oc)<650:blocked.append(row)
   rows.append(row)
   t=unreal.Transform(location=unreal.Vector(x,y,z+th/2),rotation=unreal.Rotator(),scale=unreal.Vector(r/50,r/50,th/100))
   t.set_editor_property("rotation",raw.get_editor_property("rotation"))
   transforms.append(t)
 assert len(rows)==136
 before=snapshot()
 manifest=dict(count=136,rows=rows,blocked=blocked,backup=str(backup),baseline=before,planned_contract="Design DEM route, NOT observed full trail",observed_contract="13 actual points 72.58m ONLY",render_instances_unchanged=True,rollback="After verified editor stop without save, reload original backed-up map. If explicit component-only rollback is needed in live unsaved world, remove ONLY receipt-owned new actor after exact path/hash/count validation; no automatic rollback.",source_sha256=digest(ROOT/"Scripts/ReconcileJuvenileTrunks.py"),new_actor_label="Reconciled juvenile fir trunks")
 target=ROOT/"Saved/Logs/juvenile-trunk-reconciliation-manifest.json";target.write_text(json.dumps(manifest,indent=2,allow_nan=False))
 (backup/"juvenile-trunk-reconciliation-manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False))
 assert not blocked,"ROUTE INTRUSION exact IDs in manifest; STOP NO BLIND ADD/MOVE OR SAVE"
 assert snapshot()==before
 cylinder=unreal.load_asset("/Engine/BasicShapes/Cylinder")
 c=_hism(sub,cylinder,"Reconciled juvenile fir trunks")
 c.set_collision_profile_name("BlockAll");c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
 c.get_owner().set_actor_hidden_in_game(True)
 c.set_visibility(False)
 assert str(c.get_collision_profile_name())=="BlockAll" and c.get_collision_enabled()==unreal.CollisionEnabled.QUERY_AND_PHYSICS
 manifest["owned_actor"]=c.get_owner().get_path_name();manifest["owned_component"]=c.get_path_name()
 target.write_text(json.dumps(manifest,indent=2,allow_nan=False))
 (backup/"juvenile-trunk-reconciliation-manifest.json").write_text(json.dumps(manifest,indent=2,allow_nan=False))
 c.add_instances(transforms,False,True)
 assert c.get_instance_count()==136 and str(c.get_collision_profile_name())=="BlockAll"
 assert c.get_collision_enabled()==unreal.CollisionEnabled.QUERY_AND_PHYSICS
 after=snapshot();owned=c.get_owner().get_path_name()
 filtered={k:v for k,v in after.items() if not k.startswith(owned+"/") and not k.startswith(owned+".") and not k.startswith(c.get_path_name()+"/")}
 changes=_exact_diff(before,filtered)
 receipt=dict(passed=False,count=c.get_instance_count(),existing_changes=changes,owned_actor=owned,owned_component=c.get_path_name(),profile=str(c.get_collision_profile_name()),enabled=str(c.get_collision_enabled()),alignment=[])
 out=ROOT/"Saved/Logs/juvenile-trunk-reconciliation-runtime.json";out.write_text(json.dumps(receipt,indent=2))
 assert not changes,"EXISTING SCENE CHANGED DO NOT SAVE"
 for row in rows:
  i=row["new_trunk_instance"];v=_numeric_transform(c.get_instance_transform(i,True));source=row["source_transform"]
  assert v["translation.x"]==source["translation.x"] and v["translation.y"]==source["translation.y"]
  bottom=v["translation.z"]-v["scale3d.z"]*50
  assert abs(bottom-row["world_ground_z"])<.03
  assert abs(v["scale3d.z"]*100-row["trunk_height_cm"])<.03
  assert abs(v["scale3d.x"]*50-row["trunk_radius_cm"])<.003
  receipt["alignment"].append(dict(index=i,actual=v,bottom_error_cm=bottom-row["world_ground_z"]))
 receipt["passed"]=True;out.write_text(json.dumps(receipt,indent=2,allow_nan=False))
 return receipt
