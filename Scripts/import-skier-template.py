"""Copy Epic's installed template mannequin at its original /Game/Characters paths.
No editor, downloads, project settings or existing differing files are touched.
"""
from pathlib import Path
import hashlib,json,re,shutil
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('D:/EpicGames/UE_5.8/Templates/TemplateResources/High/Characters/Content')
OUT=ROOT/'Content/Characters'
queue=['/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple']
seen=set(); receipt=[]; optional=set()
while queue:
    asset=queue.pop()
    if asset in seen: continue
    seen.add(asset)
    relative=Path(asset.removeprefix('/Game/Characters/')+'.uasset')
    source=SOURCE/relative
    if not source.is_file():
        optional.add(asset); continue
    destination=OUT/relative
    data=source.read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:
        raise RuntimeError(f'Refusing to overwrite changed asset {destination}')
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists(): shutil.copy2(source,destination)
    receipt.append(dict(path=str(destination.relative_to(ROOT)),bytes=len(data),sha256=digest))
    for dependency in re.findall(rb'/Game/[A-Za-z0-9_/]+',data):
        dependency=dependency.decode()
        if dependency.startswith('/Game/Characters/'): queue.append(dependency)
        else: optional.add(dependency)
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'template-import-receipt.json').write_text(json.dumps(dict(source=str(SOURCE),assets=receipt,unavailable_editor_only_references=sorted(optional)),indent=2))
print(f'PHASE2_ASSETS {len(receipt)} files {sum(r["bytes"] for r in receipt)} bytes')
print('Optional source editor references',sorted(optional))
