"""Pure-Python shots from ACTUAL saved world-cm population and supplied DEM.
No Unreal import or launch. Return named pitch/yaw/roll, not positional Rotator.
"""
import math,json
from pathlib import Path
def shots(height):
 r=json.loads(Path('D:/FallLine/Saved/Logs/alpine-population.json').read_text())
 trees=[dict(t) for t in r['pines']]
 moved=json.loads(Path('D:/FallLine/Saved/Logs/forest-edge-structural-plan.json').read_text())
 for row in moved['rows']:
  trees[row['index']]=dict(row['proposed'])
 assert trees
 tree=min(trees,key=lambda t:math.hypot(t['x']+8500,t['y']))
 x,y,z,h=tree['x'],tree['y'],tree['z'],tree['height_cm']
 def frame(name,px,py,pz,tx,ty,tz,fov):
  # Lift actual camera above DEM without moving the actual crown target.
  pz=max(pz,float(height(px,py))+220)
  dx,dy,dz=tx-px,ty-py,tz-pz
  return {'name':name,'location':[px,py,pz],
    'rotation':{'pitch':math.degrees(math.atan2(dz,math.hypot(dx,dy))),'yaw':math.degrees(math.atan2(dy,dx)),'roll':0},
    'fov':fov,'target':[tx,ty,tz],
    'tree_world':tree,'actor_label':'Healthy mature evergreen forest','mesh_suffix':'SM_MatureFirA'}
 # From cleared ski corridor toward the nearest actual crown; no terrain assumption.
 sign=1 if y>=0 else -1
 return [
 frame('fir-close',x-450,y-sign*1250,z+h*.68,x,y,z+h*.68,48),
 frame('fir-medium',x-2400,y-sign*4200,z+h*1.05,x,y,z+h*.60,56),
 frame('forest-wide',x-11500,0,max(z+h*3,float(height(x-11500,0))+4200),x+6000,y,z+h*.65,72)]
