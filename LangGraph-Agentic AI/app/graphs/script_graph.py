from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.nodes.script_nodes import (
    evaluate_script,
    generate_logline,
    generate_outline,
    request_human_approval,
    revise_script,
    write_script,
)
from app.schemas.state import ScriptState


def _route_after_eval(state: ScriptState) -> str:
    score = float(state.get("quality_score", 0.0))
    threshold = float(state.get("quality_threshold", 8.0))
    revision_count = int(state.get("revision_count", 0))
    max_revisions = int(state.get("max_revisions", 2))

    if score >= threshold or revision_count >= max_revisions:
        return "approval"
    return "revise"


def _route_after_approval(state: ScriptState) -> str:
    if bool(state.get("approved", False)):
        return "done"

    revision_count = int(state.get("revision_count", 0))
    max_revisions = int(state.get("max_revisions", 2))
    if revision_count >= max_revisions:
        return "done"
    return "revise"


def build_script_graph():
    builder = StateGraph(ScriptState)

    builder.add_node("generate_logline", generate_logline)
    builder.add_node("generate_outline", generate_outline)
    builder.add_node("write_script", write_script)
    builder.add_node("evaluate_script", evaluate_script)
    builder.add_node("revise_script", revise_script)
    builder.add_node("request_human_approval", request_human_approval)

    builder.add_edge(START, "generate_logline")
    builder.add_edge("generate_logline", "generate_outline")
    builder.add_edge("generate_outline", "write_script")
    builder.add_edge("write_script", "evaluate_script")

    builder.add_conditional_edges(
        "evaluate_script",
        _route_after_eval,
        {
            "approval": "request_human_approval",
            "revise": "revise_script",
        },
    )

    builder.add_edge("revise_script", "evaluate_script")

    builder.add_conditional_edges(
        "request_human_approval",
        _route_after_approval,
        {
            "done": END,
            "revise": "revise_script",
        },
    )

    return builder.compile()
