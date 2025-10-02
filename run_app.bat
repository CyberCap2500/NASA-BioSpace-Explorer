@echo off
echo NASA Space Biology Knowledge Engine
echo =====================================
echo.
echo Starting the app automatically...
echo.

REM Check if PowerShell is available
powershell -Command "& {.\run_app.ps1}"

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error running the app!
    echo Please try running: powershell -ExecutionPolicy Bypass -File run_app.ps1
    echo.
    pause
)
