@echo off
chcp 65001 > nul
setlocal
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ------------------------------------------
echo   Anime Prompt Manager
echo   http://localhost:5500
echo   Ctrl+C to stop
echo ------------------------------------------
python web_app_anime.py
endlocal
