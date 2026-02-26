@echo off
title SimpleMMO 24/7 Quest Runner
cls
:: SimpleMMO Auto-Quest Runner
:: Automatically completes quests in order from lowest to highest level

echo ============================================================
echo SimpleMMO Auto-Quest Runner
echo ============================================================
echo.

:: Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    if not exist "venv\Scripts\activate.bat" (
        echo Error: Virtual environment not found!
        echo Please run setup.bat first to install dependencies.
        echo.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    call venv\Scripts\activate.bat
)

echo Virtual environment activated
echo.

:: Check if config.json exists
if not exist "config.json" (
    echo Error: config.json not found!
    echo Please create config.json with your login credentials.
    echo See config.template.json for an example.
    echo.
    pause
    exit /b 1
)

:: Quick dependency check
python -c "import selenium" 2>nul
if errorlevel 1 (
    echo.
    echo ============================================================
    echo Missing Dependencies Detected!
    echo ============================================================
    echo.
    echo The quest runner requires additional Python packages.
    echo.
    echo Please run ONE of the following:
    echo   1. install_quest_deps.bat    ^(Quick - Quest only^)
    echo   2. pip install -r requirements.txt  ^(Full - All features^)
    echo.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo Starting quest runner...
echo.
echo This will automatically:
echo  - Fetch all available quests
echo  - Complete quests in order (lowest level first)
echo  - Move to next quest after completion
echo  - Continue until all incomplete quests are done
echo.
echo Press Ctrl+C to stop at any time
echo.
echo ============================================================
echo.

:: Run the quest runner
:start
python quest_runner.py

echo.
echo ============================================================
echo  Quest runner stopped.
echo ============================================================
echo.
echo  Press 'Enter' to restart
echo  otherwise it will auto restarting in 10 seconds...
echo.
echo  Press 'P' to pause (wait indefinitely)
echo  Press 'C' to close
echo.

:: Wait for key press with timeout (10 seconds)
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; $key=$null; $sw=[System.Diagnostics.Stopwatch]::new(); $sw.Start(); while($sw.Elapsed.TotalSeconds -lt 10 -and $key -eq $null){ if([Console]::KeyAvailable){ $key=[Console]::ReadKey($true); if($key.Key -eq 'P'){ Write-Host 'Paused. Press any key to continue...'; [Console]::ReadKey($true) | Out-Null; exit 0 } elseif($key.Key -eq 'C'){ exit 1 } }; Start-Sleep -Milliseconds 100 }; if($key -eq $null){ exit 2 }"
if errorlevel 2 goto start
if errorlevel 1 goto end

:: Auto restart
goto start

:end
echo.
echo Goodbye!
echo.
