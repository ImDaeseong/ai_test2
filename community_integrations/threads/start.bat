@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_COMMAND="
where python >nul 2>nul
if not errorlevel 1 set "PYTHON_COMMAND=python"

if not defined PYTHON_COMMAND (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_COMMAND=py -3"
)

if not defined PYTHON_COMMAND (
  echo.
  echo Python 3 could not be found.
  echo Install Python 3, then run this file again.
  echo.
  pause
  exit /b 1
)

echo.
echo Threads Studio is starting.
echo URL: http://127.0.0.1:8765/publisher.html
echo Close this window or press Ctrl+C to stop the server.
echo.

if not defined THREADS_STUDIO_NO_BROWSER start "" "http://127.0.0.1:8765/publisher.html"
%PYTHON_COMMAND% serve.py

if errorlevel 1 (
  echo.
  echo Threads Studio could not start. See the message above.
  pause
  exit /b 1
)
