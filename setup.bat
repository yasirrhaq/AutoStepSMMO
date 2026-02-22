@echo off
REM SimpleMMO Bot Setup Script for Windows

echo ========================================
echo SimpleMMO Bot - Quick Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Create virtual environment (optional but recommended)
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo WARNING: Could not create virtual environment
    echo Continuing with global Python installation...
) else (
    echo Virtual environment created successfully
    call venv\Scripts\activate.bat
)
echo.

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To use the bot:
echo 1. Edit config.json with your credentials
echo 2. Run: python simplemmo_bot.py
echo.
echo For examples: python examples.py
echo.
pause
