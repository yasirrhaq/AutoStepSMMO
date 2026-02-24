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
choice /c RC /t 10 /d R /m "Press R to Restart, C to Close (auto-restart in 10s)"
if errorlevel 2 goto end
goto start

:end
echo.
echo Goodbye!
echo.
