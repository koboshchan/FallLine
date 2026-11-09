import pathlib,sys,json,hashlib,array,math,datetime
ROOT=pathlib.Path('D:/FallLine'); DATA=ROOT/'SourceAssets/DEM'
sys.path.insert(0,str(ROOT/'Scripts'))
import PrepareRealDEM as d
import subprocess
subprocess.run(['powershell','-NoProfile','-Command','Wait-Process -Id 182332 -ErrorAction SilentlyContinue'],capture_output=True)
assert (DATA/'prepare-result.txt').read_bytes().replace(b'\x00',b'').replace(b'\xff\xfe',b'').strip()==b'0', 'DEM preparation failed'
route=json.loads((DATA/'route-selection.json').read_text())
assert len(route['heights_m'])==81 and route['heights_m'][0]-route['heights_m'][-1]>=350
fine=[dict(distance_m=i,x=-8500+i*100,y=0,z=d.height(-8500+i*100,0)) for i in range(0,2001,5)]
grades=[-(b['z']-a['z'])/500 for a,b in zip(fine,fine[1:])]
assert max(grades[:24])<1.0 and min(grades[:24])>-.1, 'Initial120m unsafe'
assert max(grades)<1.3 and min(grades)>-.25, 'Full2km line needs review'
assert fine[0]['z']-fine[-1]['z']>35000, 'Insufficient descent'
proof=dict(samples=fine,grades=grades,descent_m=(fine[0]['z']-fine[-1]['z'])/100,initial120m_max_grade=max(grades[:24]),full2km_max_grade=max(grades),full2km_min_grade=min(grades))
(DATA/'route-proof.json').write_text(json.dumps(proof,indent=2))
(DATA/'route-approved.txt').write_text('Verified numeric full2km route; no physics modifications')
m=json.loads((DATA/'manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=array.array('H');a.frombytes((DATA/'verbier.r16').read_bytes())
m.update(stac_url='https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.swissalti3d',units='cm',license_file='swisstopo-license.txt',license_sha256=sha(DATA/'swisstopo-license.txt'),
 stac_sha256=sha(DATA/'swiss-stac-full.json'),numpy_sha256=sha(DATA/'verbier-meters.npy'),
 preview_sha256=sha(DATA/'heightmap-preview.png'),cpp_sha256=sha(ROOT/'Source/FallLine/MountainBuilder.cpp'),
 acquisition_complete=True,world_height_range_cm=[(min(a)-32768)*1000/128,(max(a)-32768)*1000/128],
 vertical_offset_cm=4619-m['spawn_source_m']*100,
 format='little-endian uint16 row-major y,x with N=2017; z_cm=(value-32768)*1000/128; raw16 authoritative; numpy float32 source meters EPSG2056, shape(2017,2017)',
 helper_sha256=sha(ROOT/'Scripts/PrepareRealDEM.py'))
m['route_proof_sha256']=sha(DATA/'route-proof.json')
m['samples']=[dict(x=x,y=y,z=d.height(x,y)) for x,y in [(-8500,0),(0,0),(1000,2300),(-503900,503900),(504000,504000),(130250,-170250)]]
m['route_dense']=[dict(x=x,y=0,z=d.height(x,0)) for x in range(-8500,191501,500)]
m['route_initial_slopes']=[(d.height(x+500,0)-d.height(x,0))/500 for x in range(-8500,1500,500)]
(DATA/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
receipt=d.validate_dependencies()
(DATA/'validation-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
print('INITIAL SLOPES',m['route_initial_slopes'])
