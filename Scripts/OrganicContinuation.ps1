$ErrorActionPreference='Stop'
$p=Get-Process -Id 174020 -ErrorAction SilentlyContinue
if ($p) {
 if ($p.Path.Replace([char]92,'/') -ne 'D:/EpicGames/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe') {exit 92}
 $p.WaitForExit()
}
$r=Get-Content D:/FallLine/Saved/Screenshots/ActualPlayer/capture-result-1794236668769938700.json -Raw | ConvertFrom-Json
if ($r.error -or !$r.captured -or !$r.cleanup_phase) {exit 93}
$other=Get-Process UnrealEditor -ErrorAction SilentlyContinue
if ($other) {exit 94}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:/FallLine/Scripts/OrganicOwnerPipeline.ps1
exit $LASTEXITCODE
