from __future__ import annotations

from app.graphs.production_graph import build_production_graph
from app.graphs.script_graph import build_script_graph


class Supervisor:
    """Simple orchestrator for chaining script and production graphs."""

    def __init__(self):
        self.script_graph = build_script_graph()
        self.production_graph = build_production_graph()

    def run(self, script_input: dict, production_input: dict | None = None) -> dict:
        script_state = self.script_graph.invoke(script_input)
        if not script_state.get("approved"):
            return {"script": script_state, "production": None}

        prod_payload = production_input or {}
        prod_payload["locked_script"] = script_state.get("draft_script", "")
        production_state = self.production_graph.invoke(prod_payload)

        return {"script": script_state, "production": production_state}
