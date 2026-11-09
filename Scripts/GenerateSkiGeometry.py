"""Original FallLine ski model, stdlib only. Coordinates are Unreal centimetres.
190cm twin-tip ski, curved shovel/tail, sidecut, steel edges and bindings.
Run with normal Python. No engine process or external assets.
"""
from pathlib import Path
import math,json,hashlib
ROOT=Path("D:/FallLine")
OUT=ROOT/"SourceAssets/Skis"
OUT.mkdir(parents=True,exist_ok=True)
verts=[]; faces=[]
def v(p):
    verts.append(p);return len(verts)
def quad(a,b,c,d,mat):
    faces.extend([(mat,(a,b,c)),(mat,(a,c,d))])
def box(cx,cy,cz,l,w,h,mat):
    ids=[v((cx+x*l/2,cy+y*w/2,cz+z*h/2))
         for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                       (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    for a,b,c,d in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        quad(ids[a],ids[b],ids[c],ids[d],mat)
rings=[]
for i in range(97):
    x=-95+190*i/96
    t=abs(x)/95
    # Sidecut is narrow underfoot, wide at shovel, rounded taper at ends.
    half=4.4+2.5*t*t
    edge_taper=max(0,(abs(x)-86)/9)
    half*=math.sqrt(max(.012,1-edge_taper*edge_taper))
    front=max(0,(x-61)/34)
    tail=max(0,(-x-72)/23)
    rise=12*front*front+4*tail*tail
    camber=.65*(1-(x/95)**2)
    z=rise+camber
    rings.append([v((x,-half,z-0.7)),v((x,half,z-0.7)),
                  v((x,half,z+0.7)),v((x,-half,z+0.7))])
for a,b in zip(rings,rings[1:]):
    quad(a[1],b[1],b[0],a[0],"GraphiteBase")
    quad(b[3],b[2],a[2],a[3],"OrangeTopsheet")
    quad(b[0],b[3],a[3],a[0],"SteelEdge")
    quad(a[2],b[2],b[1],a[1],"SteelEdge")
quad(*reversed(rings[0]),"SteelEdge")
quad(*rings[-1],"SteelEdge")
# Visible toe wings, heel cup, mounting rails and raised release units.
box(-13,0,2.0,37,7.0,1.4,"GraphiteBase")
box(7,0,3.5,9,7.8,3.4,"SteelEdge")
for side in [-1,1]:
    box(7,side*3.4,5.3,7,1.5,3.3,"GraphiteBase")
    box(-24,side*3.1,5.2,7,1.4,4.4,"SteelEdge")
box(-28,0,5.0,5,7.5,5.0,"GraphiteBase")
box(-28,0,8.1,6,4.2,1.2,"OrangeTopsheet")
# Heel brake arms.
for side in [-1,1]:
    box(-17,side*4.7,1.1,13,.6,.6,"SteelEdge")
lines=["# Original FallLine geometry. Centimetres. No third-party asset.",
       "mtllib ski.mtl","o AlpineSki"]
lines += ["v %.6f %.6f %.6f"%p for p in verts]
# Explicit UV for every vertex, required by the UE Interchange OBJ translator.
lines += ["vt %.6f %.6f" % ((x+95)/190, (y+7)/14) for x,y,z in verts]
last=None
for mat,ids in faces:
    if mat!=last: lines.append("usemtl "+mat);last=mat
    lines.append("f "+" ".join(f"{i}/{i}" for i in ids))
obj=OUT/"ski.obj";obj.write_text("\n".join(lines)+"\n")
(OUT/"ski.mtl").write_text(
    "newmtl OrangeTopsheet\nKd 0.95 0.15 0.025\n"
    "newmtl GraphiteBase\nKd 0.025 0.035 0.05\n"
    "newmtl SteelEdge\nKd 0.48 0.53 0.58\n")
assert all(all(math.isfinite(q) for q in p) for p in verts)
assert max(p[0] for p in verts)-min(p[0] for p in verts)==190
report=dict(vertices=len(verts),triangles=len(faces),length_cm=190,
    width_cm=max(p[1] for p in verts)-min(p[1] for p in verts),
    rise_cm=max(p[2] for p in verts),sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),
    license="Original generated FallLine geometry, no third-party asset")
(OUT/"geometry-proof.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report))
