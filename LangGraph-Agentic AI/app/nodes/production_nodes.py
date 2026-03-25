from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.schemas.state import ProductionState
from app.services.tts_service import TTSService
from app.services.video_service import VideoService

_tts = TTSService()
_video = VideoService()


def parse_script_to_scenes(state: ProductionState) -> ProductionState:
    script = state.get("locked_script", "")
    scenes = []
    for idx, chunk in enumerate(
        [line for line in script.splitlines() if line.strip().startswith(("INT.", "EXT."))],
        start=1,
    ):
        scenes.append({"scene_id": idx, "heading": chunk.strip(), "summary": chunk.strip()})

    if not scenes:
        scenes = [{"scene_id": 1, "heading": "INT. DEFAULT SET - DAY", "summary": "Fallback scene."}]

    return {"scenes": scenes}


def create_shot_list(state: ProductionState) -> ProductionState:
    scenes = state.get("scenes", [])
    shot_list: List[Dict[str, Any]] = []
    for scene in scenes:
        scene_id = scene["scene_id"]
        shot_list.extend(
            [
                {"scene_id": scene_id, "shot_id": f"{scene_id}-A", "type": "wide", "duration_sec": 4},
                {"scene_id": scene_id, "shot_id": f"{scene_id}-B", "type": "close-up", "duration_sec": 3},
            ]
        )
    return {"shot_list": shot_list}


def generate_storyboard_prompts(state: ProductionState) -> ProductionState:
    shot_list = state.get("shot_list", [])
    prompts = [
        f"Cinematic {shot['type']} shot, scene {shot['scene_id']}, dramatic lighting, 24fps, film grain"
        for shot in shot_list
    ]
    return {"storyboard_prompts": prompts}


def generate_voiceover(state: ProductionState) -> ProductionState:
    """Generate real audio files via gTTS for each scene."""
    scenes = state.get("scenes", [])
    narration_chunks = [scene["summary"] for scene in scenes]
    voiceover_files: List[str] = []

    for scene in scenes:
        out_path = f"data/audio/voice_scene_{scene['scene_id']}.mp3"
        saved = _tts.synthesize(text=scene["summary"], output_file=out_path)
        voiceover_files.append(saved)

    return {"narration_chunks": narration_chunks, "voiceover_files": voiceover_files}


_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def generate_video_clips(state: ProductionState) -> ProductionState:
    """Generate video clips via the configured backend (local GPU, Replicate, or stub)."""
    shot_list = state.get("shot_list", [])
    storyboard_prompts = state.get("storyboard_prompts", [])
    clips: List[str] = []
    failed_shots: List[Dict[str, Any]] = []

    for idx, shot in enumerate(shot_list):
        prompt = storyboard_prompts[idx] if idx < len(storyboard_prompts) else shot["type"]
        out_path = f"data/video/clip_{shot['shot_id']}.mp4"
        try:
            saved = _video.generate_clip(prompt=prompt, output_file=out_path)
            # Only accept real video files; stub .txt files go to failed_shots
            if Path(saved).suffix.lower() in _VIDEO_EXTENSIONS:
                clips.append(saved)
            else:
                failed_shots.append({"shot_id": shot["shot_id"], "stub_file": saved,
                                      "reason": "stub mode — set VIDEO_BACKEND in .env"})
        except Exception as exc:
            failed_shots.append({"shot_id": shot["shot_id"], "error": str(exc)})

    return {"video_clips": clips, "failed_shots": failed_shots}


def assemble_timeline(state: ProductionState) -> ProductionState:
    timeline_path = Path("data/renders/timeline.json")
    timeline_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "clips": state.get("video_clips", []),
        "voiceover": state.get("voiceover_files", []),
        "music": state.get("music_file", ""),
    }
    timeline_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"timeline_file": str(timeline_path)}


def render_final_movie(state: ProductionState) -> ProductionState:
    """Concatenate video clips and stitch with first voiceover track using moviepy."""
    from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips

    output_path = Path("data/renders/final_movie.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    video_clips = [p for p in state.get("video_clips", []) if Path(p).exists()]
    voiceover_files = [p for p in state.get("voiceover_files", []) if Path(p).exists()]

    if not video_clips:
        # No real clips available yet — write a manifest instead of crashing.
        fallback = output_path.with_suffix(".txt")
        fallback.write_text("No video clips were generated. Check GPU/VRAM availability.\n")
        return {"final_movie_file": str(fallback)}

    mv_clips = [VideoFileClip(c) for c in video_clips]
    final = concatenate_videoclips(mv_clips, method="compose")

    if voiceover_files:
        audio = AudioFileClip(voiceover_files[0])
        # Trim audio to match video length
        audio = audio.subclipped(0, min(audio.duration, final.duration))
        final = final.with_audio(audio)

    final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)

    for c in mv_clips:
        c.close()

    return {"final_movie_file": str(output_path)}
