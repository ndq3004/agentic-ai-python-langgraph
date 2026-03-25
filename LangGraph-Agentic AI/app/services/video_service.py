from __future__ import annotations

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Backend selection
#
# Set VIDEO_BACKEND in your .env to choose how clips are generated:
#   local    — Wan2.1 via local GPU (requires NVIDIA GPU + CUDA drivers)
#   replicate — Wan2.1 via Replicate cloud API (requires REPLICATE_API_TOKEN)
#   stub     — No real video; creates empty placeholder file (default)
# ---------------------------------------------------------------------------
VIDEO_BACKEND = os.getenv("VIDEO_BACKEND", "stub")


class VideoService:
    """Video clip generation with pluggable local/cloud/stub backends."""

    def generate_clip(
        self,
        prompt: str,
        output_file: str,
        num_frames: int = 49,
        fps: int = 16,
        guidance_scale: float = 5.0,
        num_inference_steps: int = 50,
    ) -> str:
        backend = VIDEO_BACKEND.lower()
        if backend == "local":
            return _generate_local(prompt, output_file, num_frames, fps, guidance_scale, num_inference_steps)
        if backend == "replicate":
            return _generate_replicate(prompt, output_file)
        return _generate_stub(prompt, output_file)


# ---------------------------------------------------------------------------
# Local GPU backend (Wan2.1 via diffusers)
# ---------------------------------------------------------------------------
_local_pipe = None


def _get_local_pipe(model_id: str = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"):
    global _local_pipe
    if _local_pipe is None:
        import torch
        from diffusers import WanPipeline

        if not torch.cuda.is_available():
            raise RuntimeError(
                "No CUDA GPU detected. Set VIDEO_BACKEND=replicate in .env to use cloud GPU, "
                "or install NVIDIA drivers and re-run."
            )
        _local_pipe = WanPipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16)
        _local_pipe.to("cuda")
    return _local_pipe


def _generate_local(
    prompt: str,
    output_file: str,
    num_frames: int,
    fps: int,
    guidance_scale: float,
    num_inference_steps: int,
) -> str:
    from diffusers.utils import export_to_video

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    pipe = _get_local_pipe()
    frames = pipe(
        prompt=prompt,
        num_frames=num_frames,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
    ).frames[0]
    export_to_video(frames, output_file, fps=fps)
    return output_file


# ---------------------------------------------------------------------------
# Replicate cloud API backend (Wan2.1 hosted GPU)
# pip install replicate
# Requires REPLICATE_API_TOKEN in .env
# ---------------------------------------------------------------------------
def _generate_replicate(prompt: str, output_file: str) -> str:
    import replicate
    import httpx

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    output = replicate.run(
        "wavespeedai/wan-2.1-t2v-480p",
        input={
            "prompt": prompt,
            "num_frames": 49,
            "guidance_scale": 5.0,
            "num_inference_steps": 30,
        },
    )
    # output is a URL string pointing to the generated video
    video_url = str(output)
    mp4_path = str(Path(output_file).with_suffix(".mp4"))
    with httpx.Client(timeout=120) as client:
        data = client.get(video_url).content
    Path(mp4_path).write_bytes(data)
    return mp4_path


# ---------------------------------------------------------------------------
# Stub backend — no real video, just an empty marker file
# ---------------------------------------------------------------------------
def _generate_stub(prompt: str, output_file: str) -> str:
    marker = str(Path(output_file).with_suffix(".stub.txt"))
    Path(marker).parent.mkdir(parents=True, exist_ok=True)
    Path(marker).write_text(
        f"[STUB] No real video generated.\nPrompt: {prompt}\n"
        "Set VIDEO_BACKEND=local or VIDEO_BACKEND=replicate in .env to generate real clips.\n"
    )
    return marker


