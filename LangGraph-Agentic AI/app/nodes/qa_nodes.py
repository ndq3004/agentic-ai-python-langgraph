from __future__ import annotations

from pathlib import Path

from app.schemas.state import ProductionState


def qa_final_output(state: ProductionState) -> ProductionState:
    final_path = state.get("final_movie_file", "")
    qa_passed = bool(final_path) and Path(final_path).exists()
    return {"qa_passed": qa_passed}
