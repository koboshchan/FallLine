@echo off
"C:/Program Files/Blender Foundation/Blender 4.4/blender.exe" --background --factory-startup --python D:/FallLine/Scripts/ExportMatureFir.py > D:/FallLine/Saved/Logs/fir-export.log 2>&1
echo %errorlevel% > D:/FallLine/Saved/Logs/fir-export-exit.txt
