@echo off
chcp 65001 > nul
setlocal
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ------------------------------------------
echo   MV Image/Video Manager
echo   http://localhost:5200
echo   Ctrl+C to stop
echo ------------------------------------------
python web_app_mv.py
endlocal
