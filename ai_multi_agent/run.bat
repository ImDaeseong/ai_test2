@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
) else if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
)

if not exist "%~dp0.env" (
    echo [WARNING] .env file not found. See .env.example.
    echo.
)

if not "%~1"=="" (
    python main.py %*
    exit /b %ERRORLEVEL%
)

:MENU
cls
echo =============================================
echo   ai_multi_agent
echo =============================================
echo.
echo  [1] create-all     (all songs)
echo  [2] create         (single song)
echo  [3] validate       (check output)
echo  ---------------------------------------------
echo  [M] Web MV         (port 5200)
echo  [N] Web Anime      (port 5500)
echo  [Q] quit
echo.
set /p CHOICE="choice: "

if /i "%CHOICE%"=="M" goto WEB_MV
if /i "%CHOICE%"=="N" goto WEB_ANIME
if /i "%CHOICE%"=="1" goto CREATE_ALL
if /i "%CHOICE%"=="2" goto CREATE
if /i "%CHOICE%"=="3" goto VALIDATE
if /i "%CHOICE%"=="Q" goto END
goto MENU

:CREATE_ALL
echo.
python main.py create-all
goto PAUSE_MENU

:CREATE
echo.
set /p INPUT_FILE="song txt file path: "
python main.py create --input "%INPUT_FILE%"
goto PAUSE_MENU

:VALIDATE
echo.
python main.py validate
goto PAUSE_MENU

:WEB_MV
echo.
echo Starting Hermes MV Web UI at http://localhost:5200 ...
python web_app_mv.py
goto PAUSE_MENU

:WEB_ANIME
echo.
echo Starting Anime Web UI at http://localhost:5500 ...
python web_app_anime.py
goto PAUSE_MENU

:PAUSE_MENU
echo.
pause
goto MENU

:END
endlocal
