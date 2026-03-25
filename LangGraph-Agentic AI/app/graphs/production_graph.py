from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.nodes.production_nodes import (
    assemble_timeline,
    create_shot_list,
    generate_storyboard_prompts,
    generate_video_clips,
    generate_voiceover,
    parse_script_to_scenes,
    render_final_movie,
)
from app.nodes.qa_nodes import qa_final_output
from app.schemas.state import ProductionState


def build_production_graph():
    builder = StateGraph(ProductionState)

    builder.add_node("parse_script_to_scenes", parse_script_to_scenes)
    builder.add_node("create_shot_list", create_shot_list)
    builder.add_node("generate_storyboard_prompts", generate_storyboard_prompts)
    builder.add_node("generate_voiceover", generate_voiceover)
    builder.add_node("generate_video_clips", generate_video_clips)
    builder.add_node("assemble_timeline", assemble_timeline)
    builder.add_node("render_final_movie", render_final_movie)
    builder.add_node("qa_final_output", qa_final_output)

    builder.add_edge(START, "parse_script_to_scenes")
    builder.add_edge("parse_script_to_scenes", "create_shot_list")
    builder.add_edge("create_shot_list", "generate_storyboard_prompts")
    builder.add_edge("generate_storyboard_prompts", "generate_voiceover")
    builder.add_edge("generate_voiceover", "generate_video_clips")
    builder.add_edge("generate_video_clips", "assemble_timeline")
    builder.add_edge("assemble_timeline", "render_final_movie")
    builder.add_edge("render_final_movie", "qa_final_output")
    builder.add_edge("qa_final_output", END)

    return builder.compile()
