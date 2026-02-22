@echo off
echo ============================================================
echo Tesseract OCR - Installation Checker
echo ============================================================
echo.

echo Checking if Tesseract is installed...
tesseract --version >nul 2>&1

if %errorlevel%==0 (
    echo ✓ Tesseract is installed!
    echo.
    tesseract --version
    echo.
    echo ============================================================
    echo Installation complete! You can now use CAPTCHA auto-solve.
    echo ============================================================
    echo.
    echo To enable it:
    echo 1. Open config.json
    echo 2. Set "auto_solve_captcha": true
    echo 3. Run: python test_captcha.py
) else (
    echo ✗ Tesseract is NOT installed or not in PATH
    echo.
    echo ============================================================
    echo Installation Instructions:
    echo ============================================================
    echo.
    echo 1. Download the installer from:
    echo    https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo 2. Look for: tesseract-ocr-w64-setup-v5.x.x.exe
    echo.
    echo 3. Run the installer
    echo.
    echo 4. Install to default location:
    echo    C:\Program Files\Tesseract-OCR\
    echo.
    echo 5. The installer should add it to PATH automatically
    echo.
    echo 6. Restart this terminal and run this script again
    echo.
    echo ============================================================
)

echo.
pause
