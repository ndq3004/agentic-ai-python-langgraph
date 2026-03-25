from __future__ import annotations

from textwrap import dedent

from app.schemas.state import ScriptState


def generate_logline(state: ScriptState) -> ScriptState:
    prompt = state.get("user_prompt", "A compelling original story")
    genre = state.get("genre", "drama")
    logline = (
        f"A {genre} story where {prompt.strip().rstrip('.')}, "
        "forcing the protagonist to choose between safety and purpose."
    )
    return {"logline": logline}


def generate_outline(state: ScriptState) -> ScriptState:
    target_minutes = max(1, int(state.get("target_minutes", 3)))
    act_count = 3 if target_minutes <= 10 else 5
    acts = []
    for idx in range(1, act_count + 1):
        acts.append(f"Act {idx}: Major turning point {idx} that raises the stakes.")
    outline = "\n".join(acts)
    return {"outline": outline}


def write_script(state: ScriptState) -> ScriptState:
    genre = state.get("genre", "drama")
    logline = state.get("logline", "")
    outline = state.get("outline", "")
    revision_count = int(state.get("revision_count", 0))

    script = dedent(
        f"""
        TITLE: Untitled {genre.title()} Project

        LOGLINE:
        {logline}

        OUTLINE:
        {outline}

        SCRIPT:
        INT. APARTMENT - NIGHT
        The protagonist stares at a blinking cursor, then makes an impossible call.

        EXT. CITY STREET - LATER
        Rain hammers the asphalt as consequences begin to unfold.

        INT. STUDIO - DAWN
        A final confrontation resolves the central conflict with emotional payoff.

        NOTES:
        Revision pass: {revision_count}
        """
    ).strip()

    return {"draft_script": script}


def evaluate_script(state: ScriptState) -> ScriptState:
    script = state.get("draft_script", "")

    coherence = 8.5 if "SCRIPT:" in script else 6.5
    pacing = 8.0 if script.count("INT.") + script.count("EXT.") >= 3 else 6.5
    continuity = 8.0 if "LOGLINE:" in script and "OUTLINE:" in script else 6.0

    quality_score = round((coherence + pacing + continuity) / 3, 2)
    feedback = "Strong structure. Improve character specificity and visual detail."

    return {"quality_score": quality_score, "feedback": feedback}


def revise_script(state: ScriptState) -> ScriptState:
    revision_count = int(state.get("revision_count", 0)) + 1
    draft_script = state.get("draft_script", "")
    feedback = state.get("feedback", "")

    revised = (
        f"{draft_script}\n\nREVISION NOTES APPLIED ({revision_count}):\n"
        f"- {feedback}\n"
        "- Added stronger motivation and scene-level tension."
    ).strip()

    return {"draft_script": revised, "revision_count": revision_count}


def request_human_approval(state: ScriptState) -> ScriptState:
    auto_approve = bool(state.get("auto_approve", True))
    approved = auto_approve
    if not auto_approve:
        return {
            "approved": False,
            "feedback": "Human review required: run with --auto-approve for MVP automation.",
        }
    return {"approved": approved}
