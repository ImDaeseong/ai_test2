@echo off
chcp 65001 > nul
setlocal
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo ------------------------------------------
echo   ai_img_video_prompt  Web UI
echo   http://localhost:5100
echo   Ctrl+C to stop
echo ------------------------------------------
python web_app.py
endlocal
