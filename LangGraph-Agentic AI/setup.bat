@echo off
REM ============================================================================
REM LangGraph Agentic AI — GPU Setup Script for Windows
REM ============================================================================
REM
REM This script initializes the project on a GPU-equipped machine for local
REM Wan2.1 video generation. Run this in PowerShell or Command Prompt.
REM
REM Prerequisites:
REM   - Python 3.10+ installed and in PATH
REM   - NVIDIA GPU with CUDA Compute Capability 7.0+ (RTX series or better)
REM   - NVIDIA drivers installed (nvidia-smi should work)
REM
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo  LangGraph Agentic AI — GPU Setup
echo ============================================================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Please install Python 3.10+ first.
    echo         Visit: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found: 
for /f "tokens=*" %%i in ('python --version') do echo     %%i

REM Check NVIDIA GPU / CUDA
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] nvidia-smi not found. NVIDIA drivers may not be installed.
    echo.
    echo To enable local GPU video generation:
    echo   1. Download NVIDIA drivers: https://www.nvidia.com/Download/driverDetails.html
    echo   2. Download CUDA Toolkit:    https://developer.nvidia.com/cuda-downloads
    echo   3. Reboot after installation
    echo   4. Run this script again
    echo.
    echo Tip: Test with 'nvidia-smi' in Command Prompt after reboot.
    set SKIP_GPU_CHECK=1
) else (
    echo [OK] NVIDIA GPU detected:
    nvidia-smi --query-gpu=name --format=csv,noheader
)

echo.

REM Detect Python executable
for /f %%i in ('where python') do set PYTHON_EXE=%%i
echo Using Python: %PYTHON_EXE%

REM Check if venv already exists
if exist ".venv" (
    echo [INFO] Virtual environment already exists. Activating...
    call .venv\Scripts\activate.bat
) else (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo [OK] Virtual environment created and activated
)

echo.
echo [INFO] Installing dependencies... (this may take 5-10 minutes)
echo.

REM Install base requirements
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

REM Install PyTorch with CUDA support (only if GPU check passed or user chose to continue)
if not "%SKIP_GPU_CHECK%"=="1" (
    echo.
    echo [INFO] Installing PyTorch with CUDA 12.8 support...
    echo         (Large download, may take 2-3 minutes)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    echo [OK] PyTorch installed
) else (
    echo.
    echo [INFO] No NVIDIA GPU detected. Installing CPU-only PyTorch...
    pip install torch torchvision torchaudio
    echo [OK] CPU-only PyTorch installed
)

REM Check if .env exists, create if not
if not exist ".env" (
    echo.
    echo [INFO] Creating .env file from .env.example...
    copy .env.example .env >nul
    echo [OK] .env created
    
    REM Set VIDEO_BACKEND to local by default
    echo [INFO] Setting VIDEO_BACKEND=local in .env...
    (
        for /f "delims=" %%a in (.env) do (
            if "%%a"=="VIDEO_BACKEND=stub" (
                echo VIDEO_BACKEND=local
            ) else (
                echo %%a
            )
        )
    ) > .env.tmp
    move /y .env.tmp .env >nul
    echo [OK] VIDEO_BACKEND set to local
) else (
    echo [INFO] .env already exists (not overwriting)
)

REM Create data directories
echo.
echo [INFO] Creating data directories...
if not exist "data\scripts" mkdir data\scripts
if not exist "data\audio" mkdir data\audio
if not exist "data\video" mkdir data\video
if not exist "data\renders" mkdir data\renders
echo [OK] Directory structure ready

echo.
echo ============================================================================
echo  Setup Complete!
echo ============================================================================
echo.
echo Next steps:
echo.
echo 1. Verify GPU support:
echo    python -c "import torch; print('CUDA:', torch.cuda.is_available())"
echo.
echo 2. Run a quick test:
echo    python -m app.cli script --prompt "Test prompt"
echo.
echo 3. Run full pipeline with video:
echo    python -m app.cli full --prompt "A detective uncovers clues in old photographs"
echo.
echo For video generation to work:
echo   - Ensure VIDEO_BACKEND=local in .env
echo   - Verify nvidia-smi works in Command Prompt
echo   - First run will download Wan2.1 model (~7GB), then generate videos
echo.
echo If you see CUDA errors:
echo   1. Run: nvidia-smi
echo   2. Confirm driver version
echo   3. Install latest NVIDIA drivers if needed
echo.
echo Troubleshooting:
echo   - No GPU detected?      Install NVIDIA drivers + CUDA
echo   - CUDA out of memory?   Reduce num_frames or num_inference_steps in code
echo   - Slow generation?      Normal for Wan2.1 (first frame ~30-60s)
echo.
echo ============================================================================
echo.

pause

endlocal
