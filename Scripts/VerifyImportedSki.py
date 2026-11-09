"""Read imported render-buffer OBJ, exporter source explicitly swaps Y/Z."""
from pathlib import Path
import json,math
import unreal
ROOT=Path("D:/FallLine")
def verify():
    mesh=unreal.load_asset("/Game/Equipment/Skis/SM_AlpineSki")
    path=ROOT/"Saved/Logs/ski-imported-render.obj"
    task=unreal.AssetExportTask()
    task.object=mesh
    task.filename=str(path)
    task.exporter=unreal.StaticMeshExporterOBJ()
    task.automated=True;task.prompt=False;task.replace_identical=True
    assert unreal.Exporter.run_asset_export_task(task),list(task.errors)
    source=[tuple(map(float,l.split()[1:4])) for l in (ROOT/"SourceAssets/Skis/ski.obj").read_text().splitlines() if l.startswith("v ")]
    exported=[]
    for l in path.read_text().splitlines():
        if l.startswith("v "):
            x,z,y=map(float,l.split()[1:4]);exported.append((x,y,z))
    assert exported and source
    error=max(min(math.dist(a,b) for b in exported) for a in source)
    reverse=max(min(math.dist(a,b) for b in source) for a in exported)
    report=dict(asset=mesh.get_path_name(),source_vertices=len(source),render_triangle_vertices=len(exported),
      max_source_to_render_cm=error,max_render_to_source_cm=reverse,
      axis_basis="EditorExporters.cpp StaticMeshExporterOBJ reads render buffer and exports X,Z,Y; reversed here",
      verified=error<.01 and reverse<.01)
    (ROOT/"Saved/Logs/ski-imported-basis-proof.json").write_text(json.dumps(report,indent=2))
    assert report["verified"],report
    return report
