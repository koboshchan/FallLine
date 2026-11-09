& powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:/FallLine/Scripts/SmokeTest.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:/FallLine/Scripts/CaptureSavedForest.ps1
exit $LASTEXITCODE
