$ErrorActionPreference='Stop'
$env:TEMP='D:/FallLine/Saved/Temp'; $env:TMP=$env:TEMP
Set-Item -Path 'Env:UE-LocalDataCachePath' -Value 'D:/FallLine/DerivedDataCache'
$env:UE_ZenDataPath='D:/FallLine/Saved/Zen'
Set-Location D:/FallLine
# Fail closed before launching any editor or touching the map.
$gateStart=Get-Date
& 'C:/Users/lucas/AppData/Local/Programs/Python/Python312/python.exe' -I D:/FallLine/Scripts/ValidateRealDEM.py *> Saved/Logs/dem-gate.log
if ($LASTEXITCODE -ne 0) { throw 'DEM dependency gate failed; see Saved/Logs/dem-gate.log. Editor NOT launched.' }
$gate=Get-Content Saved/Logs/dem-gate.json | ConvertFrom-Json
if ($gate.Status -ne 'Passed' -or [datetimeoffset]$gate.Time -lt ([datetimeoffset]$gateStart).ToUniversalTime()) { throw 'Missing/stale DEM gate receipt; editor NOT launched' }
@{Started=(Get-Date).ToString('o');PID=$PID;Status='Running';ExitCode=$null} | ConvertTo-Json | Set-Content Saved/Logs/map-result.json
& 'D:/EpicGames/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' D:/FallLine/FallLine.uproject '-EditorSettingsINI=D:/FallLine/Saved/IsolatedUser/EditorSettings.ini' '-EditorKeyBindingsINI=D:/FallLine/Saved/IsolatedUser/EditorKeyBindings.ini' '-EditorLayoutINI=D:/FallLine/Saved/IsolatedUser/EditorLayout.ini' -run=pythonscript '-script=D:/FallLine/Scripts/CreateTestLevel.py' -unattended -nullrhi -nosound -NoSplash '-Abslog=D:/FallLine/Saved/Logs/map-generation.log' *> Saved/Logs/map-stdout.log
$code=$LASTEXITCODE
@{ExitCode=$code;Finished=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content Saved/Logs/map-result.json
exit $code
