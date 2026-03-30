"""
GPU / VRAM availability check for the LangGraph-Agentic AI video pipeline.

Usage:
    python check_gpu.py

Checks:
  1. PyTorch installation and version
  2. CUDA availability
  3. GPU name and total VRAM
  4. Free VRAM right now
  5. Minimum VRAM requirement for Wan2.1-T2V-1.3B (local backend)
  6. Current VIDEO_BACKEND setting
"""

import os
import sys

# ── 1. PyTorch ──────────────────────────────────────────────────────────────
print("=" * 60)
print("GPU / VRAM Diagnostic")
print("=" * 60)

try:
    import torch
    print(f"[OK] PyTorch {torch.__version__}")
except ImportError:
    print("[FAIL] PyTorch is NOT installed.")
    print("       Run:  pip install torch --index-url https://download.pytorch.org/whl/cu121")
    sys.exit(1)

# ── 2. CUDA ──────────────────────────────────────────────────────────────────
cuda_available = torch.cuda.is_available()
if cuda_available:
    print(f"[OK] CUDA available — version {torch.version.cuda}")
else:
    print("[FAIL] CUDA is NOT available.")
    print("       Possible causes:")
    print("         • No NVIDIA GPU in this machine")
    print("         • NVIDIA drivers not installed  (https://www.nvidia.com/drivers)")
    print("         • PyTorch was installed without CUDA support")
    print("           Run: pip install torch --index-url https://download.pytorch.org/whl/cu121")
    print()
    print("       Workaround: set VIDEO_BACKEND=replicate in your .env file")
    print("                   to use cloud GPU via Replicate API instead.")
    sys.exit(1)

# ── 3. GPU info ───────────────────────────────────────────────────────────────
gpu_count = torch.cuda.device_count()
print(f"[OK] {gpu_count} GPU(s) detected")

MIN_VRAM_GB = 8.0  # Wan2.1-T2V-1.3B practical minimum

all_ok = True
for i in range(gpu_count):
    props        = torch.cuda.get_device_properties(i)
    total_gb     = props.total_memory / 1024**3
    reserved_gb  = torch.cuda.memory_reserved(i) / 1024**3
    allocated_gb = torch.cuda.memory_allocated(i) / 1024**3
    free_gb      = total_gb - reserved_gb

    status = "[OK]  " if total_gb >= MIN_VRAM_GB else "[WARN]"
    print(f"\n  GPU {i}: {props.name}")
    print(f"    {status} Total  VRAM : {total_gb:.1f} GB  (minimum needed: {MIN_VRAM_GB:.0f} GB)")
    print(f"    [INFO] Reserved    : {reserved_gb:.1f} GB")
    print(f"    [INFO] Allocated   : {allocated_gb:.1f} GB")
    print(f"    [INFO] Free (est.) : {free_gb:.1f} GB")

    if total_gb < MIN_VRAM_GB:
        all_ok = False
        print(f"    --> Not enough VRAM for local Wan2.1 inference.")
        print(f"        Set VIDEO_BACKEND=replicate in .env to use cloud GPU.")

# ── 4. nvidia-smi (extra detail) ─────────────────────────────────────────────
print()
try:
    import subprocess
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        print("[OK] nvidia-smi output:")
        for line in result.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 4:
                name, total, free, driver = parts
                print(f"       Name={name}  Total={total} MiB  Free={free} MiB  Driver={driver}")
            else:
                print(f"       {line}")
    else:
        print("[WARN] nvidia-smi returned an error:", result.stderr.strip())
except FileNotFoundError:
    print("[WARN] nvidia-smi not found in PATH — install NVIDIA drivers.")
except Exception as e:
    print(f"[WARN] Could not run nvidia-smi: {e}")

# ── 5. Current .env VIDEO_BACKEND setting ────────────────────────────────────
print()
backend = os.getenv("VIDEO_BACKEND", "<not set — defaults to 'stub'>")
print(f"[INFO] VIDEO_BACKEND = {backend}")
if backend in ("stub", "<not set — defaults to 'stub'>"):
    print("       --> No real video will be generated.")
    print("           Set VIDEO_BACKEND=local  (requires NVIDIA GPU with >=8 GB VRAM)")
    print("        or VIDEO_BACKEND=replicate  (requires REPLICATE_API_TOKEN in .env)")

# ── 6. Summary ───────────────────────────────────────────────────────────────
print()
print("=" * 60)
if cuda_available and all_ok:
    print("RESULT: GPU looks ready for local video generation.")
    print("        Make sure VIDEO_BACKEND=local is set in your .env file.")
elif cuda_available and not all_ok:
    print("RESULT: GPU found but VRAM may be too low for local inference.")
    print("        Recommended: set VIDEO_BACKEND=replicate in .env.")
else:
    print("RESULT: No usable GPU — cannot run local backend.")
    print("        Recommended: set VIDEO_BACKEND=replicate in .env.")
print("=" * 60)
