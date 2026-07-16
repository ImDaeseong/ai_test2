@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv\Scripts\python.exe not found.
    echo Create the virtual environment and install requirements before running this file.
    pause
    exit /b 1
)

echo Starting Music Insight Studio...
echo Opening http://127.0.0.1:8765 in your browser.
echo Press Ctrl+C in this window to stop the server.
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul & start "" "http://127.0.0.1:8765""

".venv\Scripts\python.exe" -m app.web.server --host 127.0.0.1 --port 8765

endlocal
