"""Deterministic smooth-noise density; no strip or rectangular priority cohort."""
import random,math,json
def noise(x,y,seed):
 def h(i,j):return random.Random((i*73856093)^(j*19349663)^seed).random()
 i=math.floor(x);j=math.floor(y);u=x-i;v=y-j;u=u*u*(3-2*u);v=v*v*(3-2*v)
 return (h(i,j)*(1-u)+h(i+1,j)*u)*(1-v)+(h(i,j+1)*(1-u)+h(i+1,j+1)*u)*v
def plan(height,dimensions,count=3200,obstacles=()):
 rng=random.Random(924251);rows=[];grid={}
 for attempt in range(400000):
  # Gaussian mixture with continuous tails, no fixed nearcamera rectangle.
  if rng.random()<.68:x=rng.gauss(16000,37000);y=rng.gauss(0,26000)
  else:x=rng.gauss(85000,65000);y=rng.gauss(0,55000)
  if not(-140000<x<280000 and -170000<y<170000):continue
  variant=rng.randrange(3);scale=rng.uniform(.7,1.3);yaw=rng.uniform(0,360)
  width,h,basez,radius,axisx,axisy=dimensions[variant];canopy=width*scale*.5
  edge=2200+2200*noise(x/15000,0,319)
  if abs(y)<edge+canopy:continue
  density=.18+.82*(.65*noise(x/14500,y/14500,917)+.35*noise(x/4100,y/4100,529))
  if rng.random()>density:continue
  z=height(x,y)
  grade=math.hypot((height(x+150,y)-height(x-150,y))/300,(height(x,y+150)-height(x,y-150))/300)
  if grade>.8:continue
  cell=(int(x//500),int(y//500))
  near=[a for dx in range(-1,2) for dy in range(-1,2) for a in grid.get((cell[0]+dx,cell[1]+dy),[])]
  if any(math.hypot(x-a["x"],y-a["y"])<500 for a in near):continue
  if any(math.hypot(x-a,y-b)<500 for a,b in obstacles):continue
  angle=math.radians(yaw);tx=x+scale*(axisx*math.cos(angle)-axisy*math.sin(angle));ty=y+scale*(axisx*math.sin(angle)+axisy*math.cos(angle))
  row=dict(tx=tx,ty=ty,trunk_ground=height(tx,ty),x=x,y=y,z=z,variant=variant,scale=scale,yaw=yaw,height=h*scale,base_z=z-basez*scale-12,radius=radius*scale,trunk_height=min(h*scale*.7,1300),canopy=canopy)
  rows.append(row);grid.setdefault(cell,[]).append(row)
  if len(rows)==count:break
 assert len(rows)==count,"Insufficient safe forest sites"
 return rows
