@echo off
title SimpleMMO 24/7 AFK Bot
cls
echo ============================================================
echo SimpleMMO 24/7 AFK Mode
echo ============================================================
echo.
echo Starting bot in continuous mode...
echo Press Ctrl+C to stop
echo.
echo ============================================================
echo.

:start
C:\Users\BugonPC\AppData\Local\Programs\Python\Python313\python.exe run_24_7.py

echo.
echo ============================================================
echo  Bot stopped.
echo ============================================================
echo.
echo  Press Enter to restart, or C to close.
echo.
:ask_afk
powershell -NoProfile -Command "$k=$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown'); if($k.VirtualKeyCode -eq 13){exit 0}elseif($k.VirtualKeyCode -eq 67){exit 1}else{exit 2}"
if errorlevel 2 goto ask_afk
if errorlevel 1 goto end
goto start

:end
echo.
echo Goodbye!
echo.
