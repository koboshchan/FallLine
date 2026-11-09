"""CC0 source fetch. Manifest URLs/sizes/MD5 obtained from Poly Haven API."""
import sys
sys.stdout=open('D:/FallLine/Saved/Logs/fir-download.log','a',buffering=1)
sys.stderr=sys.stdout
import json,hashlib,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path('D:/FallLine/SourceAssets/PolyHaven/fir_tree_01')
m=json.loads((ROOT/'source-manifest.json').read_text())
def fetch(f):
 p=ROOT/f['path'];p.parent.mkdir(parents=True,exist_ok=True)
 def valid():
  return p.exists() and p.stat().st_size==f['size'] and hashlib.md5(p.read_bytes()).hexdigest()==f['md5']
 if not valid():
  req=urllib.request.Request(f['url'],headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=180) as src,p.with_suffix(p.suffix+'.part').open('wb') as out:
   while True:
    b=src.read(1024*1024)
    if not b:break
    out.write(b)
  p.with_suffix(p.suffix+'.part').replace(p)
 assert valid(),str(p)
 print('VERIFIED',f['path'],flush=True)
 return {'path':f['path'],'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
with ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(fetch,m['files']))
(ROOT/'download-result.json').write_text(json.dumps(result,indent=2))
