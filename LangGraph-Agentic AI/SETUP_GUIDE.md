# Setup Guide: GPU & Docker Deployment

This guide helps you set up this LangGraph Agentic AI project on a computer with an NVIDIA GPU for local, real-time video generation.

---

## 1. Prerequisites

Before running the setup script, ensure your GPU machine has:

- **Windows 10/11** (64-bit)
- **Python 3.10+** installed and in PATH
- **NVIDIA GPU** with CUDA Compute Capability 7.0+
  - RTX series (RTX 2070, 3070, 4070, etc.) ✅
  - A100, H100 ✅
  - Check your GPU: https://developer.nvidia.com/cuda-gpus
- **NVIDIA Drivers** (latest recommended)
- **CUDA Toolkit 12.1+**

### Check if NVIDIA drivers are installed:

```powershell
nvidia-smi
```

Should output GPU info. If not found, download drivers:
https://www.nvidia.com/Download/driverDetails.html

### Check if CUDA Toolkit is installed:

```powershell
nvcc --version
```

If "nvcc not found", download CUDA:
https://developer.nvidia.com/cuda-downloads

---

## 2. Clone & Navigate to Project

```powershell
git clone <your-repo-url> "LangGraph-Agentic-AI"
cd "LangGraph-Agentic-AI"
```

---

## 3. Run Setup (Choose One)

### Option A: Batch Script (Recommended for beginners)

Double-click `setup.bat` in Windows Explorer, or run in Command Prompt:

```cmd
setup.bat
```

This will:
- Detect Python and GPU
- Create a virtual environment
- Install all dependencies
- Set up `.env` with `VIDEO_BACKEND=local`
- Create `/data` directories

### Option B: PowerShell Script

```powershell
# First time only: allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run setup
.\setup.ps1
```

### Option C: Manual Setup

If scripts don't work, run these commands:

```powershell
# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install deps
pip install --upgrade pip
pip install -r requirements.txt

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Create .env
copy .env.example .env
# Edit .env and set: VIDEO_BACKEND=local

# Create directories
mkdir data\scripts, data\audio, data\video, data\renders
```

---

## 4. Verify GPU Setup

After setup completes, run:

```powershell
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0))"
```

Should print:
```
CUDA Available: True
GPU: NVIDIA RTX 4070 (or your GPU model)
```

If CUDA is False, NVIDIA drivers or CUDA Toolkit are missing.

---

## 5. Test the Pipeline

### Quick test (no video generation):

```powershell
python -m app.cli script --prompt "A detective finds a hidden message"
```

Expected output: Script text with quality score.

### Full pipeline with video:

```powershell
python -m app.cli full --prompt "A young editor discovers signals in old film reels"
```

Expected output: 
- Generated script saved to `data/scripts/script_*.txt`
- Audio files in `data/audio/voice_scene_*.mp3`
- Video clips in `data/video/clip_*.mp4`
- Final render in `data/renders/final_movie.mp4`

**Note:** First run downloads Wan2.1 model (~7GB). Subsequent runs use cached model.

Generation time: ~30-60 seconds per 4-second clip (normal for Wan2.1).

---

## 6. Configuration (`.env` File)

Customize behavior by editing `.env`:

```ini
# Video backend: stub | local | replicate
VIDEO_BACKEND=local

# If using Replicate cloud GPU instead:
# VIDEO_BACKEND=replicate
# REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxx

# LLM providers (optional for now)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

---

## 7. Troubleshooting

### CUDA not found after install

```powershell
# Restart your machine—CUDA PATH is set during installation
# Then re-run the setup script
```

### VRAM out of memory

Reduce model/generation size in [app/services/video_service.py](app/services/video_service.py):

```python
# In _generate_local(), reduce:
num_frames=25,  # was 49
num_inference_steps=20,  # was 50
```

Or use `VIDEO_BACKEND=replicate` for cloud GPU (pays per second).

### Very slow video generation

First run is slow (~60s) because the model is downloaded and compiled. Subsequent runs use cache.

If GPU not being used, verify:
```powershell
nvidia-smi
```

Should show python process under "Processes" section.

### Python not found

```powershell
# Option 1: Add Python to PATH manually
# Option 2: Run from Python installation directory:
C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe -m app.cli full --prompt "..."
```

---

## 8. Next: Deploy to Cloud (Optional)

Once local setup works, you can deploy to AWS/Azure/GCP:

### Docker approach (recommended):

Create `Dockerfile` at project root (example):

```dockerfile
FROM nvidia/cuda:12.1.1-runtime-windows-ltsc2022

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

ENV VIDEO_BACKEND=local

CMD python -m app.cli full --prompt "Automated video generation"
```

Then build & run:

```powershell
docker build -t langgraph-ai:latest .
docker run --gpus all langgraph-ai:latest
```

---

## 9. Quick Reference

| Command | Purpose |
|---|---|
| `python -m app.cli script --prompt "..."` | Generate script only |
| `python -m app.cli movie --script-file data/scripts/script_xyz.txt` | Generate video from saved script |
| `python -m app.cli full --prompt "..."` | Full pipeline (script → video) |
| `python -m app.cli full --prompt "..." --json` | Output as JSON |
| `nvidia-smi` | Check GPU status |
| `python -c "import torch; print(torch.cuda.is_available())"` | Check CUDA |

---

## 10. Support

If you encounter issues:

1. Check `.env` has `VIDEO_BACKEND=local`
2. Run `nvidia-smi` to verify GPU
3. Run `python -m app.cli script --prompt "test"` (no video) to isolate issues
4. Check logs for specific error messages
5. See Troubleshooting section above
