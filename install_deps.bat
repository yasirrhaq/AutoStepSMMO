@echo off
echo ============================================================
echo Installing CAPTCHA Dependencies
echo ============================================================
echo.

echo Step 1: Installing Pillow (PIL)...
C:\Users\BugonPC\AppData\Local\Programs\Python\Python313\python.exe -m pip install Pillow
echo.

echo Step 2: Installing pytesseract...
C:\Users\BugonPC\AppData\Local\Programs\Python\Python313\python.exe -m pip install pytesseract
echo.

echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Next step: Install Tesseract OCR binary
echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo After installing Tesseract, run: python test_captcha.py
echo.
pause
