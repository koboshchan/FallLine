"""Blender UV and source-alpha proof. No generated mapping."""
import bpy, numpy as np
from collections import Counter
def prove(tree,alpha_path):
 mesh=tree.data
 assert len(mesh.uv_layers)>0,"Fir has no original UV layers"
 uv=mesh.uv_layers.active
 assert uv and len(uv.data)==len(mesh.loops)
 a=np.empty(len(uv.data)*2,dtype=np.float32);uv.data.foreach_get('uv',a);a=a.reshape(-1,2)
 image=bpy.data.images.load(str(alpha_path),check_existing=True)
 pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
 pixels=pixels.reshape(image.size[1],image.size[0],4)
 result=[]
 for idx,slot in enumerate(tree.material_slots):
  loops=[li for p in mesh.polygons if p.material_index==idx for li in p.loop_indices]
  assert loops,"Empty material part"
  coords=a[loops]
  r={"material":slot.material.name,"polygons":sum(p.material_index==idx for p in mesh.polygons),"uv_loop_count":len(loops),"uv_min":coords.min(axis=0).tolist(),"uv_max":coords.max(axis=0).tolist(),"uv_std":coords.std(axis=0).tolist()}
  assert np.isfinite(coords).all() and max(r["uv_std"])>.001
  if "twig" in slot.material.name.lower():
   # Both vertices and triangle interiors. UE samples texture v from top;
   # Blender image pixels use bottom-up and source UV accordingly.
   polys=[p for p in mesh.polygons if p.material_index==idx]
   stride=max(1,len(polys)//60000)
   q=[]
   for p in polys[::stride]:
    c=a[list(p.loop_indices)]
    q.extend([c.mean(axis=0),c[0]*.6+c[1]*.2+c[2]*.2,c[0]*.2+c[1]*.6+c[2]*.2])
   q=np.asarray(q);ix=((q[:,0]%1)*image.size[0]).astype(int);iy=((q[:,1]%1)*image.size[1]).astype(int)
   mask=pixels[iy,ix,0]
   r.update(alpha_samples=len(mask),alpha_above_clip033=float((mask>=.333).mean()),alpha_mean=float(mask.mean()),alpha_std=float(mask.std()),alpha_min=float(mask.min()),alpha_max=float(mask.max()))
   print("FIR_ALPHA_PROOF",r,flush=True)
   assert r["alpha_above_clip033"]>.03 and r["alpha_std"]>.001,"Degenerate twig UV alpha lookup"
  result.append(r)
 return result
