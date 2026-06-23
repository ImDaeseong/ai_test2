@echo off
chcp 65001 > nul
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

REM ── Python으로 input/ 첫 번째 곡 폴더 탐색 ──────────────────────────────
python -c "import os,sys; d=[x for x in os.listdir('input') if os.path.isdir(os.path.join('input',x))]; print(d[0],end='') if d else sys.exit(1)" > "%TEMP%\capcut_song.tmp" 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] input/ 폴더에 곡 폴더가 없습니다.
    echo         input\{곡명}\ 폴더를 만들고 LRC 와 clips\ 를 준비하세요.
    echo.
    del "%TEMP%\capcut_song.tmp" 2>nul
    pause
    exit /b 1
)
set /p SONG=<"%TEMP%\capcut_song.tmp"
del "%TEMP%\capcut_song.tmp" 2>nul

echo.
echo ================================================
echo   ai_img_video_prompt_capcut
echo   곡: %SONG%
echo ================================================

REM ── STEP 1: build ────────────────────────────────────────────────────
echo.
echo [1/2] timeline.json 생성 중...
echo.
python main.py build --song "%SONG%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] build 실패. 위 오류를 확인하세요.
    pause
    exit /b 1
)

REM ── STEP 2: export-draft ─────────────────────────────────────────────
echo.
echo [2/2] CapCut 드래프트 생성 중...
echo       (CapCut이 실행 중이라면 지금 종료하세요)
echo.
python main.py export-draft --song "%SONG%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] export-draft 실패. 위 오류를 확인하세요.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   완료
echo   CapCut 실행 후 프로젝트 목록에서
echo   '%SONG%_MV' 를 확인하세요.
echo ================================================
echo.
pause
endlocal
