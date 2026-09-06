@echo off
setlocal
cd /d "%~dp0app"

if not exist "package.json" goto missing_project
where.exe npm.cmd >nul 2>nul
if errorlevel 1 goto missing_npm
if not exist "node_modules" goto missing_modules

echo Starting CareerDiff...
echo The browser will open at http://localhost:3000.
echo Press Ctrl+C to stop the server.
echo.

start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 60;$i++){try{$null=Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:3000' -TimeoutSec 1; Start-Process 'http://localhost:3000'; exit}catch{Start-Sleep -Milliseconds 500}}"
call npm.cmd run dev
if errorlevel 1 goto start_failed
goto end

:missing_project
echo ERROR: app\package.json was not found.
goto failed

:missing_npm
echo ERROR: Node.js and npm were not found in PATH.
goto failed

:missing_modules
echo ERROR: Dependencies are not installed.
echo Run npm install inside the app directory first.
goto failed

:start_failed
echo.
echo ERROR: CareerDiff failed to start.

:failed
pause
exit /b 1

:end
endlocal
