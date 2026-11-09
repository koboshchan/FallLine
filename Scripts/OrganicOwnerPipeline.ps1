$ErrorActionPreference='Stop'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:/FallLine/Scripts/ApplyOrganicOwner.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$r=Get-Content D:/FallLine/Saved/Logs/organic-owner-apply.json -Raw | ConvertFrom-Json
if (!$r.passed -or !$r.saved) { exit 91 }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:/FallLine/Scripts/CaptureSavedForest.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:/FallLine/Scripts/SmokeTest.ps1
exit $LASTEXITCODE
