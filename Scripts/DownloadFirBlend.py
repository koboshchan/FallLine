import json,urllib.request,hashlib
from pathlib import Path
r=Path('D:/FallLine/SourceAssets/PolyHaven/fir_tree_01')
f=json.loads((r/'blend-source-manifest.json').read_text())['files'][0]
p=r/f['path']
with urllib.request.urlopen(urllib.request.Request(f['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=180) as src,p.with_suffix('.blend.part').open('wb') as dst:
 while True:
  b=src.read(1048576)
  if not b:break
  dst.write(b)
p.with_suffix('.blend.part').replace(p)
assert p.stat().st_size==f['size'] and hashlib.md5(p.read_bytes()).hexdigest()==f['md5']
(r/'blend-download-result.json').write_text(json.dumps({'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
