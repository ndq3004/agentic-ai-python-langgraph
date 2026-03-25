from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class ScriptState(TypedDict, total=False):
    user_prompt: str
    genre: str
    target_minutes: int
    quality_threshold: float
    max_revisions: int
    revision_count: int
    auto_approve: bool
    logline: str
    outline: str
    draft_script: str
    quality_score: float
    feedback: str
    approved: bool


class ProductionState(TypedDict, total=False):
    script_id: str
    locked_script: str
    scenes: List[Dict[str, Any]]
    shot_list: List[Dict[str, Any]]
    storyboard_prompts: List[str]
    narration_chunks: List[str]
    voiceover_files: List[str]
    video_clips: List[str]
    music_file: str
    timeline_file: str
    final_movie_file: str
    qa_passed: bool
    failed_shots: List[Dict[str, Any]]


def build_initial_script_state(
    user_prompt: str,
    genre: str = "drama",
    target_minutes: int = 3,
    quality_threshold: float = 8.0,
    max_revisions: int = 2,
    auto_approve: bool = True,
) -> ScriptState:
    return {
        "user_prompt": user_prompt,
        "genre": genre,
        "target_minutes": target_minutes,
        "quality_threshold": quality_threshold,
        "max_revisions": max_revisions,
        "revision_count": 0,
        "auto_approve": auto_approve,
    }
