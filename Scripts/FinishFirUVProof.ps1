$ErrorActionPreference = 'Stop'
Start-Transcript -Path D:/FallLine/Saved/Logs/fir-uv-finish.log -Force
try {
    # Wait only for our own offline Blender export, never touch UE.
    $p = Get-Process -Id 130288 -ErrorAction SilentlyContinue
    if ($p -and $p.Path -eq 'C:\Program Files\Blender Foundation\Blender 4.4\blender.exe') { Wait-Process -Id $p.Id }
    & 'C:/Program Files/Blender Foundation/Blender 4.4/blender.exe' --background --factory-startup --python D:/FallLine/Scripts/ExportMatureFir.py *> D:/FallLine/Saved/Logs/fir-export-final.log
    if ($LASTEXITCODE -ne 0) { throw 'Offline exporter process failed' }
    if (!(Test-Path D:/FallLine/SourceAssets/PolyHaven/fir_tree_01/fir-export-corner-uv.npy)) { throw 'Final UV snapshot absent' }
    & 'C:/Program Files/Blender Foundation/Blender 4.4/blender.exe' --background --factory-startup --python D:/FallLine/Scripts/CheckMatureFir.py *> D:/FallLine/Saved/Logs/fir-roundtrip-final.log
    if ($LASTEXITCODE -ne 0) { throw 'Roundtrip process failed' }
    & 'C:/Users/lucas/miniconda3/python.exe' D:/FallLine/Scripts/ValidateAlpineDependencies.py *> D:/FallLine/Saved/Logs/fir-uv-final-gate.log
    if ($LASTEXITCODE -ne 0) { throw 'Final strict UV gate failed; HOLD REMAP' }
    '{"passed":true,"unreal_launched":false}' | Set-Content D:/FallLine/Saved/Logs/fir-uv-finish-result.json
} catch {
    @{passed=$false;error=$_.ToString();unreal_launched=$false}|ConvertTo-Json|Set-Content D:/FallLine/Saved/Logs/fir-uv-finish-result.json
    throw
} finally { Stop-Transcript }
