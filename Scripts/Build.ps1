$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$env:TEMP='D:/FallLine/Saved/Temp'; $env:TMP=$env:TEMP
Set-Item -Path 'Env:UE-LocalDataCachePath' -Value 'D:/FallLine/DerivedDataCache'
$env:UE_ZenDataPath='D:/FallLine/Saved/Zen'
New-Item -ItemType Directory -Force $env:TEMP,'D:/FallLine/Saved/Logs' | Out-Null
Set-Location D:/FallLine
@{Started=(Get-Date).ToString('o');PID=$PID} | ConvertTo-Json | Set-Content Saved/Logs/build-start.json
@{Status='Running';Started=(Get-Date).ToString('o');ExitCode=$null;PID=$PID} | ConvertTo-Json | Set-Content Saved/Logs/build-result.json
& 'D:/EpicGames/UE_5.8/Engine/Build/BatchFiles/Build.bat' FallLineEditor Win64 Development '-Project=D:/FallLine/FallLine.uproject' -WaitMutex -NoHotReloadFromIDE -Compiler=VisualStudio2022 -MaxParallelActions=6 '-UBARootDir=D:/FallLine/Saved/UBA' '-Log=D:/FallLine/Saved/Logs/UBT-Editor.log' *> Saved/Logs/build-editor.log
$code=$LASTEXITCODE
@{ExitCode=$code;Finished=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content Saved/Logs/build-result.json
exit $code
