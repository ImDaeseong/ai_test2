@echo off
setlocal
set "PYTHONUTF8=1"
set "PYTHONUNBUFFERED=1"
set "PATH=%PATH%;%APPDATA%\Python\Python39\Scripts"
cd /d "%~dp0"
echo Starting... please wait.
echo.
python -u run.py search 30
echo.
explorer output\reports
pause
endlocal