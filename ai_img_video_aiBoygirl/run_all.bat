@echo off
chcp 65001 > nul
cd /d "%~dp0"
set PYTHONUTF8=1

echo.
echo ================================================================
echo   STEP 1/2  --  create-all
echo ================================================================
python main.py create-all --input-dir input --force
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] create-all failed.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   STEP 2/2  --  validate_output
echo ================================================================
python validate_output.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Validation found issues. Check output above.
)

echo.
pause
