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
echo  Bot stopped. Restarting in 10 seconds...
echo  Press Ctrl+C NOW to exit completely.
echo ============================================================
timeout /t 10 /nobreak >nul
goto start
