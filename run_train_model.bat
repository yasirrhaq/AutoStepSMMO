@echo off
:: SimpleMMO CAPTCHA Model Training Script
:: Trains/fine-tunes the CLIP model using labeled captcha attempts

echo ============================================================
echo SimpleMMO CAPTCHA Model Training
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

:: Check if captcha_learning directory exists
if not exist "captcha_learning" (
    echo Warning: captcha_learning directory not found!
    echo.
    echo The training script needs labeled captcha attempts to train on.
    echo Please run the bot first to collect some captcha data.
    echo.
    pause
    exit /b 1
)

:: Check for required dependencies
echo Checking dependencies...
python -c "import torch, transformers, PIL" 2>nul
if errorlevel 1 (
    echo.
    echo ============================================================
    echo Missing Dependencies Detected!
    echo ============================================================
    echo.
    echo The model training requires additional Python packages:
    echo   - torch (PyTorch)
    echo   - transformers (Hugging Face)
    echo   - pillow (Image processing)
    echo.
    echo Installing required packages...
    echo.
    pip install torch transformers pillow
    echo.
    if errorlevel 1 (
        echo Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo Starting Model Training
echo ============================================================
echo.
echo This will:
echo  - Load labeled captcha attempts from captcha_learning/
echo  - Fine-tune the CLIP model on your data
echo  - Save the improved model for the bot to use
echo.
echo Note: Training may take several minutes depending on:
echo  - Number of training samples
echo  - Your hardware (GPU/CPU)
echo  - Model size
echo.
echo Press Ctrl+C to cancel
echo.
echo ============================================================
echo.

:: Run the training script
python train_captcha_model.py

echo.
echo ============================================================
echo Training Complete
echo ============================================================
echo.

:: Check the exit code
if errorlevel 1 (
    echo.
    echo Error occurred during training.
    echo Please check the output above for details.
    echo.
) else (
    echo.
    echo Success! The trained model is ready to use.
    echo The bot will automatically use the improved model.
    echo.
)

pause
