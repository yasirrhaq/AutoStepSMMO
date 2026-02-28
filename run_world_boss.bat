@echo off
title World Boss Bot SMMO
cls
REM World Boss Bot Launcher
REM Automatically attacks world bosses when they become available

echo ============================================
echo SimpleMMO - World Boss Bot
echo ============================================
echo.
echo This bot will:
echo - Check for attackable world bosses
echo - Auto-attack when bosses are available
echo - Track damage, EXP, and gold rewards
echo.
echo Press Ctrl+C to stop at any time
echo.
pause

python world_boss_bot.py

if errorlevel 1 (
    echo.
    echo Script exited with error. Press any key to exit...
    pause >nul
)
