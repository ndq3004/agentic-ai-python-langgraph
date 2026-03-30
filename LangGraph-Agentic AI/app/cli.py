from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.graphs.production_graph import build_production_graph
from app.graphs.script_graph import build_script_graph
from app.schemas.state import build_initial_script_state

# Load environment variables from .env file
load_dotenv()


def _ensure_data_dirs() -> None:
    for rel in ["data/scripts", "data/audio", "data/video", "data/renders"]:
        Path(rel).mkdir(parents=True, exist_ok=True)


def run_script_flow(args: argparse.Namespace) -> dict:
    graph = build_script_graph()
    payload = build_initial_script_state(
        user_prompt=args.prompt,
        genre=args.genre,
        target_minutes=args.target_minutes,
        quality_threshold=args.quality_threshold,
        max_revisions=args.max_revisions,
        auto_approve=args.auto_approve,
    )
    return graph.invoke(payload)


def run_movie_flow(args: argparse.Namespace, script_text: str) -> dict:
    graph = build_production_graph()
    payload = {
        "script_id": args.script_id,
        "locked_script": script_text,
        "music_file": args.music_file,
        "failed_shots": [],
    }
    return graph.invoke(payload)


def command_script(args: argparse.Namespace) -> int:
    _ensure_data_dirs()
    state = run_script_flow(args)

    print("\n=== SCRIPT FLOW RESULT ===")
    print(f"Approved: {state.get('approved', False)}")
    print(f"Quality score: {state.get('quality_score', 0)}")
    print("\n--- Draft Script ---\n")
    print(state.get("draft_script", ""))

    if args.save_script:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = Path("data/scripts") / f"script_{timestamp}.txt"
        file_path.write_text(state.get("draft_script", ""), encoding="utf-8")
        print(f"\nSaved script to: {file_path}")

    return 0


def command_movie(args: argparse.Namespace) -> int:
    _ensure_data_dirs()

    if args.script_file:
        script_text = Path(args.script_file).read_text(encoding="utf-8")
    else:
        script_text = "INT. STUDIO - DAY\nFallback script text."

    state = run_movie_flow(args, script_text)

    print("\n=== MOVIE FLOW RESULT ===")
    print(f"Final artifact: {state.get('final_movie_file')}")
    print(f"QA passed: {state.get('qa_passed', False)}")
    print(f"Timeline: {state.get('timeline_file')}")

    return 0


def command_full(args: argparse.Namespace) -> int:
    _ensure_data_dirs()

    script_state = run_script_flow(args)
    print("\n=== SCRIPT FLOW RESULT ===")
    print(f"Approved: {script_state.get('approved', False)}")
    print(f"Quality score: {script_state.get('quality_score', 0)}")

    script_text = script_state.get("draft_script", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_file = Path("data/scripts") / f"script_{timestamp}.txt"
    script_file.write_text(script_text, encoding="utf-8")

    if not script_state.get("approved", False):
        print("\nScript not approved. Skipping movie flow.")
        return 0

    movie_state = run_movie_flow(args, script_text)

    print("\n=== MOVIE FLOW RESULT ===")
    print(f"Script file: {script_file}")
    print(f"Final artifact: {movie_state.get('final_movie_file')}")
    print(f"QA passed: {movie_state.get('qa_passed', False)}")

    if args.json:
        print("\n=== JSON OUTPUT ===")
        print(json.dumps({"script": script_state, "movie": movie_state}, indent=2))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LangGraph Agentic AI MVP CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_shared_flags(p: argparse.ArgumentParser) -> None:
        p.add_argument("--prompt", default="A reluctant hero must stop a citywide blackout conspiracy")
        p.add_argument("--genre", default="thriller")
        p.add_argument("--target-minutes", type=int, default=3)
        p.add_argument("--quality-threshold", type=float, default=8.0)
        p.add_argument("--max-revisions", type=int, default=2)
        p.add_argument("--auto-approve", action="store_true", default=True)
        p.add_argument("--manual-approval", action="store_true", help="Disable auto approval and force graph stop at approval gate")
        p.add_argument("--script-id", default="mvp-script-001")
        p.add_argument("--music-file", default="data/audio/music_track.wav")

    p_script = sub.add_parser("script", help="Run only the script graph")
    add_shared_flags(p_script)
    p_script.add_argument("--save-script", action="store_true")
    p_script.set_defaults(func=command_script)

    p_movie = sub.add_parser("movie", help="Run only the movie graph")
    add_shared_flags(p_movie)
    p_movie.add_argument("--script-file", default="")
    p_movie.set_defaults(func=command_movie)

    p_full = sub.add_parser("full", help="Run script graph then movie graph")
    add_shared_flags(p_full)
    p_full.add_argument("--json", action="store_true")
    p_full.set_defaults(func=command_full)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "manual_approval", False):
        args.auto_approve = False
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
