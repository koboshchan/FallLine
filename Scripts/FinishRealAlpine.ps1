$ErrorActionPreference='Stop'
Set-Location D:/FallLine
Start-Transcript -Path Saved/Logs/real-alpine-pipeline.log -Append
$pipelineStart=Get-Date
function Require-FreshResult($path,$started) {
  $r=Get-Content $path | ConvertFrom-Json
  if($null -eq $r.ExitCode -or $r.ExitCode -ne 0 -or -not $r.Finished -or [datetimeoffset]$r.Finished -lt $started) { throw "Missing/failed/stale result $path" }
}
function Run-Stage($script,$result) {
  $stageStart=Get-Date
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script
  if($LASTEXITCODE -ne 0) { throw "Stage process failed $script" }
  Require-FreshResult $result $stageStart
}
try {
  $expectedBuild=[datetimeoffset]'2026-11-09T11:57:25Z'
  while((Get-ScheduledTask -TaskName FallLine-Build).State -eq 'Running') { Start-Sleep 5 }
  Require-FreshResult Saved/Logs/build-result.json $expectedBuild
  $start=Get-Content Saved/Logs/build-start.json|ConvertFrom-Json
  if([datetimeoffset]$start.Started -lt $expectedBuild){throw 'Build start stale'}
  $hashes=Get-Content Saved/Logs/real-dem-build-source.json|ConvertFrom-Json
  foreach($prop in $hashes.PSObject.Properties){
    if((Get-FileHash $prop.Name -Algorithm SHA256).Hash.ToLower() -ne $prop.Value){throw "Source changed since build $($prop.Name)"}
  }
  Run-Stage Scripts/GenerateMap.ps1 Saved/Logs/map-result.json
  Run-Stage Scripts/SmokeTest.ps1 Saved/Logs/smoke-result.json
  Run-Stage Scripts/CaptureMountain.ps1 Saved/Logs/capture-process.json
  $receipt='Saved/Screenshots/AlpineCorrected/capture-result.json'
  if(-not(Test-Path $receipt) -or (Get-Item $receipt).LastWriteTime -lt $pipelineStart){throw 'Overview receipt stale or missing'}
  Run-Stage Scripts/CapturePlayer.ps1 Saved/Logs/player-capture-process.json
  @{Status='Finished';Started=$pipelineStart.ToString('o');Finished=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content Saved/Logs/real-alpine-pipeline-result.json
} catch {
  @{Status='Failed';Error=$_.Exception.Message;Started=$pipelineStart.ToString('o');Finished=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content Saved/Logs/real-alpine-pipeline-result.json
} finally { Stop-Transcript }
