$ErrorActionPreference='Stop'
$env:TEMP='D:/FallLine/Saved/Temp'; $env:TMP=$env:TEMP
Set-Item -Path 'Env:UE-LocalDataCachePath' -Value 'D:/FallLine/DerivedDataCache'
$env:UE_ZenDataPath='D:/FallLine/Saved/Zen'
Set-Location D:/FallLine
@{Started=(Get-Date).ToString('o');PID=$PID;Status='Running';ExitCode=$null} | ConvertTo-Json | Set-Content Saved/Logs/smoke-result.json
& 'D:/EpicGames/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' D:/FallLine/FallLine.uproject '-EditorSettingsINI=D:/FallLine/Saved/IsolatedUser/EditorSettings.ini' '-EditorKeyBindingsINI=D:/FallLine/Saved/IsolatedUser/EditorKeyBindings.ini' '-EditorLayoutINI=D:/FallLine/Saved/IsolatedUser/EditorLayout.ini' /Game/Maps/TestSlope -game -nullrhi -nosound -unattended -NoSplash -FallLineSmoke -NoLoadingScreen -UseFixedTimeStep -FPS=60 '-ExecCmds=t.IdleWhenNotForeground 0' '-Abslog=D:/FallLine/Saved/Logs/smoke.log' *> Saved/Logs/smoke-stdout.log
$code=$LASTEXITCODE
@{ExitCode=$code;Finished=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content Saved/Logs/smoke-result.json
exit $code
