import bpy,json,math,hashlib
from pathlib import Path
R=Path("D:/FallLine/SourceAssets/PolyHaven/fir_tree_01")
for variant in "abc":
 f=R/("fir_single_"+variant+".fbx")
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(f))
 m=next(o for o in bpy.context.scene.objects if o.type=="MESH")
 slots={i for i,s in enumerate(m.material_slots) if "trunk" in s.material.name.lower()}
 inds={i for p in m.data.polygons if p.material_index in slots for i in p.vertices}
 pts=[m.matrix_world@m.data.vertices[i].co for i in inds];assert pts
 zmin=min(p.z for p in pts)
 section=[p for p in pts if zmin+.25<=p.z<=zmin+1.25]
 assert len(section)>=10
 # Author trunk centre from lower-stem crosssection, independently pergeometry.
 xmin=min(p.x for p in section);xmax=max(p.x for p in section);ymin=min(p.y for p in section);ymax=max(p.y for p in section)
 x=(xmin+xmax)/2;y=(ymin+ymax)/2
 radius=max(math.hypot(p.x-x,p.y-y) for p in section)
 out=dict(verified=True,variant=variant,fbx_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),axis_x_cm=x*100,axis_y_cm=y*100,radius_cm=radius*100,section_z_metres=[zmin+.25,zmin+1.25],sample_vertices=len(section),method="Actual trunk-material lowerstem crosssection bounds centre and enclosingradius; not crown geometry")
 (R/("trunk-origin-"+variant+".json")).write_text(json.dumps(out,indent=2));print(out,flush=True)
