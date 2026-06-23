@echo off
cd /d "%~dp0"

echo.
echo ============================================
echo   ai_img_video_prompt_capcut
echo   MV CapCut Timeline Generator
echo ============================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

python -c "import click" > nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing click...
    pip install click -q
)

python -c "import mutagen" > nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing mutagen...
    pip install mutagen -q
)

echo.

if not "%~1"=="" (
    echo [SONG] %~1
    echo.
    echo --- inspect ---
    python main.py inspect --song "%~1"
    echo.
    echo --- plan ---
    python main.py plan --song "%~1"
    echo.
    echo --- build ---
    python main.py build --song "%~1"
    echo.
    echo Done. Check output\%~1\
    pause
    exit /b 0
)

echo [ALL] Processing all songs in input\...
echo.
python main.py build-all
echo.
echo Done. Check output\
echo.
pause
