$ErrorActionPreference='Stop'
$env:TEMP='D:/FallLine/Saved/Temp'; $env:TMP=$env:TEMP
Set-Item -Path 'Env:UE-LocalDataCachePath' -Value 'D:/FallLine/DerivedDataCache'
$env:UE_ZenDataPath='D:/FallLine/Saved/Zen'
Set-Location D:/FallLine
@{Started=(Get-Date).ToString('o');PID=$PID;Status='Running'} | ConvertTo-Json | Set-Content Saved/Logs/capture-process.json
& 'D:/EpicGames/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' D:/FallLine/FallLine.uproject '-EditorSettingsINI=D:/FallLine/Saved/IsolatedUser/EditorSettings.ini' '-EditorKeyBindingsINI=D:/FallLine/Saved/IsolatedUser/EditorKeyBindings.ini' '-EditorLayoutINI=D:/FallLine/Saved/IsolatedUser/EditorLayout.ini' /Game/Maps/TestSlope '-ExecutePythonScript=D:/FallLine/Scripts/CaptureMountain.py' -unattended -nosound -NoSplash -NoLoadingScreen -windowed -ResX=1600 -ResY=900 '-ExecCmds=t.IdleWhenNotForeground 0' '-Abslog=D:/FallLine/Saved/Logs/capture.log' *> Saved/Logs/capture-stdout.log
@{ExitCode=$LASTEXITCODE;Finished=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content Saved/Logs/capture-process.json
