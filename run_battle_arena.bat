@echo off
title SimpleMMO Battle Arena Bot
cd /d "%~dp0"

echo ============================================================
echo  SimpleMMO Battle Arena Bot
echo ============================================================
echo.

:: Activate the virtual environment
if exist "..\..\.venv\Scripts\activate.bat" (
    call "..\..\.venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

:start
echo Starting Battle Arena Bot...
echo Press Ctrl+C to stop.
echo.

python battle_arena_bot.py

echo.
echo ============================================================
echo  Bot stopped.
echo ============================================================
echo.
choice /c RC /t 10 /d R /m "Press R to Restart, C to Close (auto-restart in 10s)"
if errorlevel 2 goto end
goto start

:end
echo.
echo Goodbye!
echo.
