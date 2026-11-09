"""Standard-library fail-closed proof gate; no Blender or Unreal imports."""
import json,hashlib
def validate_uv(base,rec):
 m=json.loads((base/'blend-source-manifest.json').read_text())
 assert m['license']=='CC0' and m['license_url']=='https://polyhaven.com/license'
 for f in m['files']:
  p=base/f['path']
  assert p.is_file() and p.stat().st_size==f['size']
  h=hashlib.md5()
  with p.open('rb') as src:
   for b in iter(lambda:src.read(1048576),b''):h.update(b)
  assert h.hexdigest()==f['md5']
 assert rec.get('uv_roundtrip_verified') and rec.get('uv_corner_order_exact'),'Fir UV proof absent'
 assert rec.get('uv_xy_roundtrip_max_error')==0
 assert rec.get('uv_recovery_source')=='fir_tree_01_1k.blend:CORNER FLOAT_VECTOR UVMap.xy'
 assert all(p['uv_loop_count']>0 for p in rec['uv_parts'])
 assert any('twig' in p['material'] and p['alpha_std']>.001 and p['alpha_above_clip033']>.03 for p in rec['uv_parts'])
