@echo off
set TEMP=D:\FallLine\Saved\Temp
set TMP=D:\FallLine\Saved\Temp
"C:/Program Files/Blender Foundation/Blender 4.4/blender.exe" --background --factory-startup --python D:/FallLine/Scripts/ExportForestFirB.py > D:/FallLine/Saved/Logs/fir-b-export.log 2>&1
echo %errorlevel% > D:/FallLine/Saved/Logs/fir-b-export.exit
"C:/Program Files/Blender Foundation/Blender 4.4/blender.exe" --background --factory-startup --python D:/FallLine/Scripts/ExportForestFirC.py > D:/FallLine/Saved/Logs/fir-c-export.log 2>&1
echo %errorlevel% > D:/FallLine/Saved/Logs/fir-c-export.exit
