$ErrorActionPreference='Stop'
$env:TEMP='D:/FallLine/Saved/Temp'; $env:TMP=$env:TEMP
Set-Item -Path 'Env:UE-LocalDataCachePath' -Value 'D:/FallLine/DerivedDataCache'
$env:UE_ZenDataPath='D:/FallLine/Saved/Zen'
Set-Location D:/FallLine
@{Started=(Get-Date).ToString('o');PID=$PID;Status='Running';ExitCode=$null} | ConvertTo-Json | Set-Content Saved/Logs/inspect-result.json
& 'D:/EpicGames/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' D:/FallLine/FallLine.uproject -run=pythonscript '-script=D:/FallLine/Scripts/InspectScene.py' -unattended -nullrhi -nosound -NoSplash '-Abslog=D:/FallLine/Saved/Logs/scene-inspection.log' *> Saved/Logs/inspect-stdout.log
@{ExitCode=$LASTEXITCODE;Finished=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content Saved/Logs/inspect-result.json
