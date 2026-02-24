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
echo  Press Enter to restart, or C to close.
echo.
:ask_arena
powershell -NoProfile -Command "$k=$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown'); if($k.VirtualKeyCode -eq 13){exit 0}elseif($k.VirtualKeyCode -eq 67){exit 1}else{exit 2}"
if errorlevel 2 goto ask_arena
if errorlevel 1 goto end
goto start

:end
echo.
echo Goodbye!
echo.
