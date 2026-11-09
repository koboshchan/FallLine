"""Real Verbier swissALTI3D preparation; runtime sampler uses only stdlib.
Run standalone Python, never in UE, to acquire/reproject data. Import height in UE.
"""
import pathlib, sys, json, math, array
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'SourceAssets'/'DEM'
N=2017
SPACING=500.0
ZSCALE=1000.0
BOUNDS=(-504000.0,-504000.0,504000.0,504000.0)
_cache=None
def height(x,y):
    global _cache
    if _cache is None:
        a=array.array('H'); a.frombytes((DATA/'verbier.r16').read_bytes())
        if sys.byteorder!='little': a.byteswap()
        if len(a)!=N*N: raise ValueError('DEM length mismatch')
        _cache=a
    gx=(x-BOUNDS[0])/SPACING; gy=(y-BOUNDS[1])/SPACING
    if not (0<=gx<=N-1 and 0<=gy<=N-1): raise ValueError('Outside real DEM bounds')
    ix=min(int(gx),N-2); iy=min(int(gy),N-2); u=gx-ix; v=gy-iy
    a=_cache[iy*N+ix]; b=_cache[iy*N+ix+1]
    c=_cache[(iy+1)*N+ix]; d=_cache[(iy+1)*N+ix+1]
    # UE landscape regular quad diagonal from (0,0) to (1,1).
    z=a+(b-a)*u+(d-b)*v if u>=v else a+(d-c)*u+(c-a)*v
    return (z-32768)*ZSCALE/128
def prepare():
    sys.path.insert(0,str(DATA/'python'))
    import numpy as np, rasterio, urllib.request, hashlib, time
    from rasterio.warp import reproject, Resampling
    from rasterio.transform import Affine
    from pyproj import Transformer
    from PIL import Image
    DATA.mkdir(parents=True,exist_ok=True)
    url='https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.swissalti3d/items?bbox=7.18,46.015,7.39,46.165&limit=100'
    features=[]
    while url:
        j=json.load(urllib.request.urlopen(url,timeout=90));features+=j['features']
        url=next((l['href'] for l in j['links'] if l['rel']=='next'),None)
    (DATA/'swiss-stac-full.json').write_text(json.dumps(features,indent=2))
    chosen={}
    for f in features:
        key=f['id'].split('_')[-1]
        if key not in chosen or f['id']>chosen[key]['id']:chosen[key]=f
    sources=[]
    for f in chosen.values():
        for name,asset in f['assets'].items():
            if not name.endswith('_2_2056_5728.tif'):continue
            p=DATA/name; expected=asset.get('file:checksum','')[4:].lower()
            if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
                urllib.request.urlretrieve(asset['href'],p)
            actual=hashlib.sha256(p.read_bytes()).hexdigest()
            if expected and actual!=expected: raise ValueError('Checksum '+name)
            sources.append(dict(file=name,url=asset['href'],sha256=actual,bytes=p.stat().st_size))
        print('ACQUIRED',len(sources),len(chosen),flush=True)
    tolv=Transformer.from_crs(4326,2056,always_xy=True)
    east,north=tolv.transform(7.284,46.083)
    # Search actual sampled terrain for a sustained straight skiable 2km descent.
    from rasterio.merge import merge
    handles=[rasterio.open(DATA/s['file']) for s in sources]
    mosaic,mt=merge(handles,res=10,nodata=-9999)
    for h in handles:h.close()
    surface=mosaic[0]
    orig_e,orig_n=east,north
    best=None
    for de in range(-1800,1801,150):
      for dn in range(-1800,1801,150):
       e=orig_e+de;n=orig_n+dn
       for k in range(48):
        angle=k*math.tau/48; ux=math.cos(angle);uy=math.sin(angle)
        ds=np.arange(0,2001,25)
        xs=e+ds*ux;ys=n+ds*uy
        cols=((xs-mt.c)/mt.a).astype(int);rows=((ys-mt.f)/mt.e).astype(int)
        if np.any(cols<0) or np.any(rows<0) or np.any(cols>=surface.shape[1]) or np.any(rows>=surface.shape[0]):continue
        zs=surface[rows,cols]
        if np.any(zs<1600) or zs[0]>3100:continue
        grades=-np.diff(zs)/25
        if grades[0]<.15 or grades[0]>.65 or np.max(grades[:8])>.8:continue
        descent=zs[0]-zs[-1]
        if descent<350 or np.max(grades)>1.0 or np.min(grades)<-.08:continue
        score=descent-5000*np.mean(np.maximum(-grades,0))-1800*np.mean(np.maximum(grades-.75,0))-abs(float(np.mean(grades))-.32)*300
        reach=5040*(abs(ux)+abs(uy))
        center_e=e+85*ux;center_n=n+85*uy
        if center_e-reach<2580000 or center_e+reach>2596000 or center_n-reach<1096000 or center_n+reach>1112000:continue
        if best is None or score>best[0]:best=(score,e,n,ux,uy,zs.tolist(),grades.tolist())
    if best is None:raise ValueError('No real ski route')
    _,east,north,route_dx,route_dy,zs,grades=best
    (DATA/'route-selection.json').write_text(json.dumps(dict(start_lv95=[east,north],direction=[route_dx,route_dy],heights_m=zs,grades=grades,score=float(best[0])),indent=2))
    def source_height(e,n):
        for s in sources:
            with rasterio.open(DATA/s['file']) as ds:
                if ds.bounds.left<=e<ds.bounds.right and ds.bounds.bottom<=n<ds.bounds.top:
                    return float(next(ds.sample([(e,n)]))[0])
        raise ValueError('No source at location')
    ge=(source_height(east+20,north)-source_height(east-20,north))/40
    gn=(source_height(east,north+20)-source_height(east,north-20))/40
    norm=math.hypot(ge,gn); dx=route_dx; dy=route_dy
    # X downhill, Y left of downhill, exact 1m source = 100cm world.
    px=-dy; py=dx
    # Spawn at local(-85m,0), chosen real coordinate.
    ce=east+85*dx; cn=north+85*dy
    step=SPACING/100; half=(N-1)*step/2
    transform=Affine(dx*step,px*step,ce-dx*(half+step/2)-px*(half+step/2),
                     dy*step,py*step,cn-dy*(half+step/2)-py*(half+step/2))
    terrain=np.full((N,N),np.nan,dtype='float32')
    for s in sources:
        with rasterio.open(DATA/s['file']) as ds:
            reproject(rasterio.band(ds,1),terrain,src_transform=ds.transform,src_crs=ds.crs,
                      dst_transform=transform,dst_crs='EPSG:2056',src_nodata=ds.nodata,
                      dst_nodata=float('nan'),resampling=Resampling.bilinear,
                      init_dest_nodata=False,num_threads=2)
    if not np.isfinite(terrain).all():raise ValueError('Incomplete DEM coverage '+str(np.isnan(terrain).sum()))
    spawnz=float(terrain[1008,991])
    world=(terrain-spawnz)*100+4619
    raw=np.rint(32768+world*128/ZSCALE)
    if raw.min()<0 or raw.max()>65535: raise ValueError('Height clipping')
    raw=raw.astype('<u2');raw.tofile(DATA/'verbier.r16')
    np.save(DATA/'verbier-meters.npy',terrain)
    # Render actual hillshade, not an illustrative procedural mountain.
    gy,gx=np.gradient(terrain,step,step);shade=np.clip((1-gx*.65-gy*.4)/np.sqrt(1+gx*gx+gy*gy),0,1)
    t=(terrain-terrain.min())/(terrain.max()-terrain.min())
    rgb=np.stack([(.22+.78*t)*shade,(.29+.71*t)*shade,(.30+.70*t)*shade],axis=-1)
    Image.fromarray((np.clip(rgb,0,1)*255).astype('uint8')).save(DATA/'heightmap-preview.png')
    Image.fromarray(raw).save(DATA/'heightmap-raw16.png')
    route=[dict(x=x,y=0,z=height(x,0)) for x in range(-8500,191501,10000)]
    manifest=dict(source='Federal Office of Topography swisstopo swissALTI3D',native_resolution_m=2,
       license='swisstopo OGD terms, commercial use allowed, attribution mandatory',
       license_url='https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices',
       attribution='©swisstopo',sources=sources,source_crs='EPSG:2056',
       source_bbox_query=[7.18,46.015,7.39,46.165],spawn_lv95=[east,north],
       downhill_unit=[dx,dy],raster_transform=list(transform),dimensions=[N,N],
       spacing_cm=SPACING,z_scale=ZSCALE,bounds_cm=BOUNDS,world_origin_cm=[-504000,-504000,0],
       raw16='verbier.r16',raw16_sha256=hashlib.sha256((DATA/'verbier.r16').read_bytes()).hexdigest(),
       source_height_min_m=float(terrain.min()),source_height_max_m=float(terrain.max()),
       spawn_source_m=spawnz,spawn_world_cm=[-8500,0,height(-8500,0)],route=route,
       modifications='Reprojection, bilinear sampling to 5m, rigid XY rotation, vertical translation, uint16 quantization. NO procedural banks or height exaggeration.',
       api='height(x,y) worldcm -> terrain worldcm; BOUNDS=(xmin,ymin,xmax,ymax)')
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (DATA/'ATTRIBUTION.txt').write_text('Terrain derived from swissALTI3D. ©swisstopo\n'+manifest['license_url']+'\n',encoding='utf-8')
    print('COMPLETE',json.dumps({k:manifest[k] for k in ['spawn_world_cm','source_height_min_m','source_height_max_m','downhill_unit','route']}),flush=True)
if __name__=='__main__': prepare()

def validate_dependencies():
    import hashlib, datetime
    assert (DATA/'prepare-result.txt').read_bytes().replace(b'\x00',b'').replace(b'\xff\xfe',b'').strip()==b'0', 'Acquisition incomplete or failed'
    def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
    m=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    assert m['dimensions']==[N,N] and m['spacing_cm']==SPACING and m['z_scale']==ZSCALE
    assert tuple(m['bounds_cm'])==BOUNDS and m['units']=='cm'
    assert m['world_origin_cm']==[-504000,-504000,0]
    assert m['sources'] and m['source_crs']=='EPSG:2056'
    assert m['stac_url']=='https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.swissalti3d'
    license_text=(DATA/m['license_file']).read_text(encoding='utf-8')
    assert len(license_text)>1500 and 'A reference to the source is mandatory' in license_text and 'used commercially' in license_text
    assert m['license_url']=='https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices'
    assert digest(DATA/m['license_file'])==m['license_sha256']
    assert digest(DATA/'swiss-stac-full.json')==m['stac_sha256']
    stac=json.loads((DATA/'swiss-stac-full.json').read_text())
    official={}
    for f in stac:
        for name,a in f['assets'].items():
            official[name]=(a['href'],a.get('file:checksum','')[4:].lower())
    for s in m['sources']:
        assert s['url'].startswith('https://data.geo.admin.ch/ch.swisstopo.swissalti3d/')
        assert official[s['file']]==(s['url'],s['sha256'])
        assert digest(DATA/s['file'])==s['sha256']
        assert (DATA/s['file']).stat().st_size==s['bytes']
    raw=(DATA/'verbier.r16').read_bytes()
    assert len(raw)==N*N*2 and digest(DATA/'verbier.r16')==m['raw16_sha256']
    assert digest(DATA/'verbier-meters.npy')==m['numpy_sha256']
    assert digest(DATA/'heightmap-preview.png')==m['preview_sha256']
    assert digest(ROOT/'Source/FallLine/MountainBuilder.cpp')==m['cpp_sha256']
    cpp=(ROOT/'Source/FallLine/MountainBuilder.cpp').read_text()
    for token in ['N=2017','Spacing=500.f, ZScale=1000.f','FVector(-504000,-504000,0)','SourceAssets/DEM/verbier.r16']:
        assert token in cpp, 'C++ transform mismatch '+token
    a=array.array('H'); a.frombytes(raw)
    if sys.byteorder!='little':a.byteswap()
    low=(min(a)-32768)*ZSCALE/128; high=(max(a)-32768)*ZSCALE/128
    assert math.isfinite(low) and math.isfinite(high) and high>low
    assert [low,high]==m['world_height_range_cm']
    global _cache
    _cache=None
    assert callable(height) and len(m['samples'])>=6
    for x,y in [(-504000,-504000),(-504000,504000),(504000,-504000),(504000,504000),(0,0),(-8500,0)]:
        z=height(x,y); assert math.isfinite(z) and low<=z<=high
        ix=int((x+504000)/500); iy=int((y+504000)/500)
        assert z==(a[iy*N+ix]-32768)*1000/128
    for x,y in [(-504001,0),(504001,0),(0,-504001),(0,504001)]:
        try: height(x,y)
        except ValueError: pass
        else: raise AssertionError('Out of bounds must raise')
    for sample in m['samples']:
        assert abs(height(sample['x'],sample['y'])-sample['z'])<1e-6
    assert abs(height(-8500,0)-4619)<4
    assert m['acquisition_complete'] is True
    assert digest(DATA/'route-proof.json')==m['route_proof_sha256']
    route=json.loads((DATA/'route-proof.json').read_text())
    assert len(route['samples'])==401 and route['descent_m']>350
    assert route['initial120m_max_grade']<1.0 and route['full2km_max_grade']<1.3 and route['full2km_min_grade']>-.25
    for pt in route['samples']:
        assert abs(height(pt['x'],pt['y'])-pt['z'])<1e-6
    return dict(status='Passed',source_count=len(m['sources']),raw16_sha256=m['raw16_sha256'],
       manifest_sha256=digest(DATA/'manifest.json'),grid_dimensions=[N,N],units='cm',
       bounds_cm=BOUNDS,height_range_cm=[low,high],spawn_ground_cm=height(-8500,0),
       callable_samples=len(m['samples']),license_sha256=m['license_sha256'],
       checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
