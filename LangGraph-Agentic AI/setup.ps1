# ============================================================================
# LangGraph Agentic AI — GPU Setup Script for Windows (PowerShell)
# ============================================================================
#
# Usage:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   .\setup.ps1
#
# Prerequisites:
#   - Python 3.10+ installed
#   - NVIDIA GPU with CUDA support
#   - NVIDIA drivers installed
#
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " LangGraph Agentic AI — GPU Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found in PATH. Install Python 3.10+ first." -ForegroundColor Red
    Write-Host "Visit: https://www.python.org/downloads/`n"
    exit 1
}

# Check NVIDIA GPU
$hasNvidia = $false
try {
    $gpuInfo = nvidia-smi --query-gpu=name --format=csv,noheader 2>&1
    if ($?) {
        Write-Host "[OK] NVIDIA GPU detected: $gpuInfo" -ForegroundColor Green
        $hasNvidia = $true
    }
} catch {
    Write-Host "[WARNING] nvidia-smi not found. Install NVIDIA drivers?" -ForegroundColor Yellow
}

if (-not $hasNvidia) {
    Write-Host ""
    Write-Host "To enable GPU video generation:" -ForegroundColor Yellow
    Write-Host "  1. Download NVIDIA drivers: https://www.nvidia.com/Download/driverDetails.html" -ForegroundColor Yellow
    Write-Host "  2. Download CUDA Toolkit:    https://developer.nvidia.com/cuda-downloads" -ForegroundColor Yellow
    Write-Host "  3. Reboot after installation" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""

# Create/activate venv
if (Test-Path ".venv") {
    Write-Host "[INFO] Virtual environment exists. Activating..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

Write-Host ""
Write-Host "[INFO] Installing dependencies... (5-10 minutes)" -ForegroundColor Cyan
Write-Host ""

# Upgrade pip
python -m pip install --upgrade pip

# Install base requirements
pip install -r requirements.txt

# Install PyTorch with CUDA
if ($hasNvidia) {
    Write-Host ""
    Write-Host "[INFO] Installing PyTorch with CUDA 12.8..." -ForegroundColor Cyan
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    Write-Host "[OK] PyTorch installed" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[INFO] No NVIDIA GPU detected. Installing CPU-only PyTorch..." -ForegroundColor Cyan
    pip install torch torchvision torchaudio
    Write-Host "[OK] CPU-only PyTorch installed" -ForegroundColor Green
}

# Create/update .env
Write-Host ""
if (-not (Test-Path ".env")) {
    Write-Host "[INFO] Creating .env from .env.example..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] .env created" -ForegroundColor Green
    
    # Set VIDEO_BACKEND=local
    $envContent = Get-Content ".env" | ForEach-Object {
        if ($_ -match "^VIDEO_BACKEND=") {
            "VIDEO_BACKEND=local"
        } else {
            $_
        }
    }
    $envContent | Set-Content ".env"
    Write-Host "[OK] VIDEO_BACKEND set to local" -ForegroundColor Green
} else {
    Write-Host "[INFO] .env already exists (not overwriting)" -ForegroundColor Cyan
}

# Create data directories
Write-Host ""
Write-Host "[INFO] Creating data directories..." -ForegroundColor Cyan
@("data\scripts", "data\audio", "data\video", "data\renders") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
    }
}
Write-Host "[OK] Directories ready" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Verify GPU support:" -ForegroundColor Cyan
Write-Host '   python -c "import torch; print('"'"'CUDA available:'"'"', torch.cuda.is_available())"' -ForegroundColor White
Write-Host ""
Write-Host "2. Quick test (no video):" -ForegroundColor Cyan
Write-Host '   python -m app.cli script --prompt "Test prompt"' -ForegroundColor White
Write-Host ""
Write-Host "3. Full pipeline with video generation:" -ForegroundColor Cyan
Write-Host '   python -m app.cli full --prompt "A detective discovers clues in photographs"' -ForegroundColor White
Write-Host ""
Write-Host "Important:" -ForegroundColor Yellow
Write-Host "  - First video generation downloads Wan2.1 model (~7GB)" -ForegroundColor Yellow
Write-Host "  - Generation takes 30-60s per clip (normal for this model)" -ForegroundColor Yellow
Write-Host "  - Ensure VIDEO_BACKEND=local in .env" -ForegroundColor Yellow
Write-Host ""
