$ErrorActionPreference='Stop'
$env:TEMP='D:/FallLine/Saved/Temp'; $env:TMP=$env:TEMP
Set-Item -Path 'Env:UE-LocalDataCachePath' -Value 'D:/FallLine/DerivedDataCache'
$env:UE_ZenDataPath='D:/FallLine/Saved/Zen'
Set-Location D:/FallLine
New-Item -ItemType Directory -Force Saved/Logs,Saved/Screenshots/ActualPlayer | Out-Null
@{Started=(Get-Date).ToString('o');PID=$PID;Status='Running';ExitCode=$null} | ConvertTo-Json | Set-Content Saved/Logs/player-ab-capture-process.json
$captureProcess=Start-Process -FilePath 'D:/EpicGames/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList @('D:/FallLine/FallLine.uproject','-EditorSettingsINI=D:/FallLine/Saved/IsolatedUser/EditorSettings.ini','-EditorKeyBindingsINI=D:/FallLine/Saved/IsolatedUser/EditorKeyBindings.ini','-EditorLayoutINI=D:/FallLine/Saved/IsolatedUser/EditorLayout.ini','/Game/Maps/TestSlope','-ExecutePythonScript=D:/FallLine/Scripts/CapturePlayerCameraAB.py','-unattended','-nosound','-NoSplash','-NoLoadingScreen','-windowed','-ResX=1600','-ResY=900','"-ExecCmds=t.IdleWhenNotForeground 0"','-Abslog=D:/FallLine/Saved/Logs/player-ab-capture.log') -Wait -PassThru -RedirectStandardOutput 'D:/FallLine/Saved/Logs/player-ab-capture-stdout.log' -RedirectStandardError 'D:/FallLine/Saved/Logs/player-ab-capture-stderr.log'
$code=$captureProcess.ExitCode
@{ExitCode=$code;Finished=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content Saved/Logs/player-ab-capture-process.json
exit $code
