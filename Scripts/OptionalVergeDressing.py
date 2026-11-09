"""Optional additive dressing only. Parent explicitly integrates after AA A/B."""
import math,random,json,hashlib
from pathlib import Path
import unreal
def plan(height,bounds,pines,seed=59072,route_xy=None):
 assert route_xy and len(route_xy)>=2,"Supply measured/approved route centerline world XY; no guessed route"
 rng=random.Random(seed);out=[];cells=set();xmin,ymin,xmax,ymax=bounds
 segments=[]
 length=0.
 for a,b in zip(route_xy,route_xy[1:]):
  vx,vy=b[0]-a[0],b[1]-a[1];l=math.hypot(vx,vy)
  assert l>0
  segments.append((a,b,vx,vy,l,length));length+=l
 def route_distance(x,y):
  best=(float("inf"),None)
  for a,b,vx,vy,l,start in segments:
   u=((x-a[0])*vx+(y-a[1])*vy)/(l*l)
   if not 0<=u<=1:continue
   d=math.hypot(x-a[0]-u*vx,y-a[1]-u*vy)
   if d<best[0]:best=(d,start+u*l)
  return best
 def route_point(distance):
  for a,b,vx,vy,l,start in segments:
   if distance<=start+l:
    u=(distance-start)/l
    return a[0]+u*vx,a[1]+u*vy,-vy/l,vx/l
  raise AssertionError("No endpoint extrapolation")
 sapling_cap=max(1,min(120,int(120*length/54000)))
 rock_cap=max(1,min(80,int(80*length/54000)))
 cluster_cap=max(2,min(24,int(24*length/54000)))
 centers=[]
 for i in range(cluster_cap):
  d=length*(i+1)/(cluster_cap+1)
  x,y,nx,ny=route_point(d)
  side=-1 if i%2 else 1
  offset=rng.uniform(1700,4000)
  centers.append((x+nx*side*offset,y+ny*side*offset,min(900,length/8)))
 for attempt in range(10000):
  if len(out)>=sapling_cap+rock_cap:break
  cx,cy,spread=centers[attempt%len(centers)]
  x=rng.gauss(cx,spread);y=rng.gauss(cy,spread*.65)
  if not xmin+200<x<xmax-200 or not ymin+200<y<ymax-200:continue
  ns=sum(t["kind"]=="sapling" for t in out);nr=len(out)-ns
  kind="sapling" if ns<sapling_cap and (nr>=rock_cap or rng.random()<.7) else "rock"
  if (kind=="sapling" and ns>=sapling_cap) or (kind=="rock" and nr>=rock_cap):continue
  target=rng.uniform(200,650) if kind=="sapling" else rng.uniform(35,95)
  width=rng.uniform(.9,1.18)
  # Source fir crown width/height <.36; use .40 conservative radius factor.
  radius=target*.40*width if kind=="sapling" else target
  distance,along=route_distance(x,y)
  if along is None or not radius+300<=along<=length-radius-300:continue
  if distance>5500:continue
  clearance=distance-radius
  if clearance<650:continue
  # Smooth probability taper measured from actual route, not a uniform Y wall.
  if rng.random()>min(1,max(0,(clearance-650)/1800))**.65:continue
  if any((p["x"]-x)**2+(p["y"]-y)**2<220**2 for p in pines):continue
  cell=(int(x//280),int(y//280))
  if cell in cells:continue
  z=float(height(x,y))
  slope=math.hypot((height(x+100,y)-height(x-100,y))/200,(height(x,y+100)-height(x,y-100))/200)
  if not math.isfinite(z) or slope>.75:continue
  cells.add(cell)
  out.append(dict(x=x,y=y,z=z,kind=kind,height_cm=target,yaw=rng.uniform(0,360),width=width,route_canopy_clearance_cm=clearance,route_along_cm=along,route_length_cm=length,canopy_radius_cm=radius))
 return out
def _numeric_transform(t):
 out={}
 for field,axes in (("translation","xyz"),("rotation","xyzw"),("scale3d","xyz")):
  v=t.get_editor_property(field)
  for axis in axes:
   n=float(v.get_editor_property(axis))
   assert math.isfinite(n),"Nonfinite transform"
   out[field+"."+axis]=n
 return out
def _exact_diff(before,after):
 changes=[]
 for key in sorted(set(before)|set(after)):
  if key not in before:changes.append(dict(path=key,kind="additional",after=after[key]))
  elif key not in after:changes.append(dict(path=key,kind="missing",before=before[key]))
  elif before[key]!=after[key]:
   changes.append(dict(path=key,kind="changed",before=before[key],after=after[key]))
 return changes
def apply(height,bounds,route_xy=None):
 assert route_xy and len(route_xy)>=2,"Route centerline approval required"
 from PopulateAlpine import _hism,_transform
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 assert not any(a.get_actor_label().startswith("Optional edge v2 ") for a in actors.get_all_level_actors()),"Already dressed, refuse duplicate"
 old=list(actors.get_all_level_actors())
 def snapshot():
  rows={}
  def transform(path,t):
   for field,value in _numeric_transform(t).items():rows[path+"/"+field]=value
  # Enumerate fresh so removed actors/components are not hidden by stale objects.
  oldpaths={a.get_path_name() for a in old}
  for a in actors.get_all_level_actors():
   ap=a.get_path_name()
   if ap not in oldpaths:
    if a.get_actor_label().startswith("Optional edge v2 "):continue
    rows[ap+"/unexpected_actor"]=True
   transform(ap+"/transform",a.get_actor_transform())
   rows[ap+"/exists"]=True
   for c in a.get_components_by_class(unreal.PrimitiveComponent):
    cp=c.get_path_name()
    transform(cp+"/transform",c.get_world_transform())
    rows[cp+"/collision_enabled"]=str(c.get_collision_enabled())
    rows[cp+"/collision_profile"]=str(c.get_collision_profile_name())
    if isinstance(c,unreal.InstancedStaticMeshComponent):
     rows[cp+"/instance_count"]=c.get_instance_count()
     for i in range(c.get_instance_count()):
      transform(cp+"/instances/"+str(i),c.get_instance_transform(i,True))
  return rows
 before=snapshot()
 population=json.loads(Path("D:/FallLine/Saved/Logs/alpine-population.json").read_text())
 items=plan(height,bounds,population["pines"],route_xy=route_xy)
 # Reuse proven UV-correct healthy fir as juvenile, never dead sapling FBX.
 forest=next(a for a in old if a.get_actor_label()=="Healthy mature evergreen forest")
 rockactor=next(a for a in old if a.get_actor_label()=="Exposed granite outcrops")
 meshes={}
 for key,a in [("sapling",forest),("rock",rockactor)]:
  meshes[key]=a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)[0].get_editor_property("static_mesh")
 for key in meshes:
  mesh=meshes[key];bb=mesh.get_bounding_box();h=bb.max.z-bb.min.z
  assert h>0
  c=_hism(actors,mesh,"Optional edge v2 "+key)
  c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
  assert str(c.get_collision_profile_name())=="NoCollision"
  assert c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
  for primitive in c.get_owner().get_components_by_class(unreal.PrimitiveComponent):
   assert primitive.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
  transforms=[]
  for t in items:
   if t["kind"]!=key:continue
   s=t["height_cm"]/h
   buried=8 if key=="sapling" else t["height_cm"]*.35
   transforms.append(_transform((t["x"],t["y"],t["z"]-bb.min.z*s-buried),(s*t["width"],s*t["width"],s),t["yaw"]))
  c.add_instances(transforms,False,True)
  assert c.get_instance_count()==len(transforms)
  assert c.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
  assert str(c.get_collision_profile_name())=="NoCollision"
  for primitive in c.get_owner().get_components_by_class(unreal.PrimitiveComponent):
   assert primitive.get_collision_enabled()==unreal.CollisionEnabled.NO_COLLISION
 after=snapshot()
 changes=_exact_diff(before,after)
 Path("D:/FallLine/Saved/Logs/optional-verge-existing-diff.json").write_text(json.dumps(dict(equal=not changes,changes=changes),indent=2,allow_nan=False))
 assert not changes,"Existing numeric scene changed; inspect optional-verge-existing-diff.json; DO NOT SAVE"
 report=dict(items=items,count=len(items),old_scene_sha256=hashlib.sha256(json.dumps(before,sort_keys=True,allow_nan=False).encode()).hexdigest(),existing_unchanged=True,new_collision="NoCollision")
 Path("D:/FallLine/Saved/Logs/optional-verge-dressing.json").write_text(json.dumps(report,indent=2))
 unreal.log("FALLLINE_OPTIONAL_VERGE "+json.dumps({k:v for k,v in report.items() if k!="items"}))
 return report
