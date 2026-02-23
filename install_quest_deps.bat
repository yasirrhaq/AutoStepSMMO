@echo off
:: Install Quest Runner Dependencies
:: Lighter than full bot - no Selenium/CAPTCHA/AI dependencies

echo ============================================================
echo Installing Quest Runner Dependencies
echo ============================================================
echo.

:: Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Using .venv virtual environment
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Using venv virtual environment
) else (
    echo No virtual environment found, using global Python
)
echo.

echo Installing core dependencies...
pip install requests>=2.31.0
pip install beautifulsoup4>=4.12.0
pip install lxml>=4.9.0
pip install brotli>=1.1.0
pip install selenium>=4.15.0
pip install webdriver-manager>=4.0.0

echo.
echo ============================================================
echo Quest Runner Dependencies Installed!
echo ============================================================
echo.
echo You can now run: run_quest.bat
echo.
pause
