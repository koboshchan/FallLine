"""Offline bounded paired-edge proposal, never launches Unreal."""
import json,math,random,hashlib
from pathlib import Path
ROOT=Path("D:/FallLine")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 from PrepareRealDEM import height
 source=ROOT/"Saved/Logs/alpine-population.json"
 p=json.loads(source.read_text())["pines"]
 design=json.loads((ROOT/"SourceAssets/DEM/manifest.json").read_text())
 planned=design["route"]
 assert planned[0]["x"]==-8500 and planned[-1]["x"]==191500
 actual=json.loads((ROOT/"Saved/Logs/player-route-pass10-worldxy.json").read_text())
 observed=[s["xy_cm"] for s in actual["samples"]]
 def dist(x,y,points):
  result=float("inf")
  for a,b in zip(points,points[1:]):
   vx,vy=b[0]-a[0],b[1]-a[1];l=vx*vx+vy*vy
   u=max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/l))
   result=min(result,math.hypot(x-a[0]-u*vx,y-a[1]-u*vy))
  return result
 rng=random.Random(84193);rows=[];occupied=[]
 for i,t in enumerate(p):
  # Planned design ONLY, no uphill extension beyond documented start.
  if not -8500<=t["x"]<=42000 or not 4500<=abs(t["y"])<9000:continue
  for attempt in range(80):
   x=t["x"]+rng.uniform(-1700,1700)
   if not -8500<=x<=42000:continue
   side=1 if t["y"]>0 else -1
   boundary=3400+1400*math.sin(x/6100+side)+850*math.sin(x/2300-side*.7)
   # Layered lobes, random pockets and irregular depth, not replacement straight strip.
   y=side*(boundary+rng.uniform(0,5200))
   target=rng.uniform(650,1500) if abs(y)<5000 else rng.uniform(1200,2400)
   width=rng.uniform(.90,1.20);radius=t["trunk_radius_cm"]*target/t["height_cm"]*width
   canopy=target*.40*width
   planned_clear=abs(y)-canopy
   actual_clear=dist(x,y,observed)-canopy
   if min(planned_clear,actual_clear)<1300:continue
   if any(math.hypot(x-a,y-b)<500 for a,b in occupied):continue
   z=height(x,y)
   grade=math.hypot((height(x+150,y)-height(x-150,y))/300,(height(x,y+150)-height(x,y-150))/300)
   if grade>.80:continue
   occupied.append((x,y))
   rows.append(dict(index=i,original=t,original_sha256=hashlib.sha256(json.dumps(t,sort_keys=True).encode()).hexdigest(),proposed=dict(x=x,y=y,z=z,height_cm=target,width=width,yaw=rng.uniform(0,360),trunk_radius_cm=radius,trunk_height_cm=min(target*.70,1300)),planned_canopy_clearance_cm=planned_clear,observed_canopy_clearance_cm=actual_clear))
   break
  else:raise AssertionError("No safe bounded proposal "+str(i))
 receipt=dict(seed=84193,region=dict(x=[-8500,42000],abs_y_original=[4500,9000]),baseline_manifest_sha256=sha(source),planned_contract="DEM manifest route derived by PrepareRealDEM.py: x=-8500..191500 y=0; SkiPawn resets X>170000; PLANNED DESIGN NOT OBSERVED",planned_sources={str(ROOT/"Scripts/PrepareRealDEM.py"):sha(ROOT/"Scripts/PrepareRealDEM.py"),str(ROOT/"Source/FallLine/SkiPawn.cpp"):sha(ROOT/"Source/FallLine/SkiPawn.cpp"),str(ROOT/"SourceAssets/DEM/manifest.json"):sha(ROOT/"SourceAssets/DEM/manifest.json")},observed_contract="13 samples 6.359sec 72.58m ONLY",observed_route_sha256=sha(ROOT/"Saved/Logs/player-route-pass10-worldxy.json"),count=len(rows),pairing="Exact same manifest index in mature crown HISM and trunk collision HISM; runtime source-derived association mandatory before mutation",rows=rows,total_tree_count=3200,outside_scope_must_remain_exact=True)
 out=ROOT/"Saved/Logs/forest-edge-structural-plan.json";out.write_text(json.dumps(receipt,indent=2));return receipt
if __name__=="__main__":
 p=build();print(json.dumps(dict(count=p["count"],ids=[r["index"] for r in p["rows"]],minimum_planned_clearance=min(r["planned_canopy_clearance_cm"] for r in p["rows"]),minimum_observed_clearance=min(r["observed_canopy_clearance_cm"] for r in p["rows"]))))
