$ErrorActionPreference='Stop'
Set-Location D:/FallLine
Start-Transcript -Path Saved/Logs/alpine-pipeline.log -Append
try {
  while((Get-ScheduledTask -TaskName FallLine-Build).State -eq 'Running' -or (Get-ScheduledTask -TaskName FallLine-Inspect).State -eq 'Running') { Start-Sleep 5 }
  $b=Get-Content Saved/Logs/build-result.json | ConvertFrom-Json
  if($b.ExitCode -ne 0 -or [datetime]$b.Finished -lt [datetime]'2026-11-09T11:26:00Z') { throw 'Fresh build not successful' }
  & ./Scripts/GenerateMap.ps1
  if((Get-Content Saved/Logs/map-result.json|ConvertFrom-Json).ExitCode -ne 0) { throw 'Map failed' }
  & ./Scripts/SmokeTest.ps1
  if((Get-Content Saved/Logs/smoke-result.json|ConvertFrom-Json).ExitCode -ne 0) { throw 'Smoke failed' }
  & ./Scripts/CaptureMountain.ps1
  if((Get-Content Saved/Logs/capture-process.json|ConvertFrom-Json).ExitCode -ne 0) { throw 'Capture process failed; inspect screenshot receipt separately' }
  if(-not (Test-Path Saved/Screenshots/AlpineCorrected/capture-result.json)) { throw 'Capture receipt missing' }
  @{Status='Finished';Time=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content Saved/Logs/alpine-pipeline-result.json
} catch {
  @{Status='Failed';Error=$_.Exception.Message;Time=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content Saved/Logs/alpine-pipeline-result.json
} finally { Stop-Transcript }
