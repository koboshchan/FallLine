"""Offline source-contract test only. Does NOT import/run Unreal or write a level."""
import sys,types,importlib.util,json,ast,hashlib
from pathlib import Path
ROOT=Path('D:/FallLine')
for name in ['CreateSnowMaterial.py','PopulateAlpine.py','ImportMatureFir.py','ExportMatureFir.py','DownloadMatureFir.py']:
 ast.parse((ROOT/'Scripts'/name).read_text())
class Vec:
 def __init__(self,x=0,y=0,z=0):self.x=x;self.y=y;self.z=z
class Box:
 min=Vec(-200,-200,0);max=Vec(200,200,1800)
class Mesh:
 def get_bounding_box(self):return Box()
class Batch:
 def __init__(self):self.count=0
 def add_instances(self,items,*args):self.count=len(items)
 def get_instance_count(self):return self.count
u=types.ModuleType('unreal')
u.Vector=Vec;u.Rotator=lambda **k:k;u.Transform=lambda **k:k
u.EditorActorSubsystem=object
u.get_editor_subsystem=lambda *a:None
u.load_asset=lambda *a:Mesh()
u.log=lambda *a:None
sys.modules['unreal']=u
f=types.ModuleType('ImportMatureFir');f.import_fir=lambda:Mesh()
sys.modules['ImportMatureFir']=f
spec=importlib.util.spec_from_file_location('TestPopulation',ROOT/'Scripts/PopulateAlpine.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod._hism=lambda *a:Batch()
mod.atmosphere=lambda *a:{'offline_stub':True}
class Sink:
 def write_text(self,text):pass
mod.Path=lambda *a:Sink()
calls=0
def sampler(x,y):
 global calls
 assert -504000<=x<=504000 and -504000<=y<=504000,(x,y)
 calls+=1
 return 2500-x*.20
report=mod.populate(Mesh(),Mesh(),sampler,(-504000,-504000,504000,504000))
assert len(report['pines'])==3200
assert all(abs(t['y'])>=4500 for t in report['pines'])
near=[t for t in report['pines'] if ((t['x']+8500)**2+t['y']**2)**.5<=60000]
assert len(near)>500,len(near)
for args in [(None,(-504000,-504000,504000,504000)),(sampler,(-504000,504000,-504000,504000))]:
 try:mod.populate(Mesh(),Mesh(),*args)
 except AssertionError:pass
 else:raise AssertionError("Invalid contract accepted")
result={'offline_only':True,'no_unreal_launched':True,'synthetic_plane_test':True,'counts':report['counts'],'within_600m_spawn':len(near),'sampler_calls':calls,'out_of_bounds_calls':0,'corridor_clear':True}
(ROOT/'Saved/Logs/alpine-source-validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
