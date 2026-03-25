# LangGraph Agentic AI: Simple to Advanced Guide

This guide helps you build an Agentic AI system with **LangGraph** that automates two major outcomes:

1. Generate a high-quality movie script from a prompt.
2. Convert the approved script into a finished movie (shots, voice, video, and final edit).

The guide is staged from simple to advanced so you can ship quickly, then harden over time.

---

## 1) What You Are Building

At a high level, your pipeline is:

**Idea -> Script Agent Flow -> Human Approval -> Movie Production Agent Flow -> Rendered Video**

With LangGraph, each step becomes a node in a stateful graph. You gain:

- Branching logic (retry, revise, fallback)
- Memory and state across the pipeline
- Human-in-the-loop checkpoints
- Observability and resumability

---

## 2) Recommended Architecture

Use two graphs:

1. **Script Graph**
- Generates concept, logline, outline, scenes, dialogue
- Scores quality and consistency
- Revises until quality threshold

2. **Movie Graph**
- Breaks script into shots
- Creates storyboard prompts
- Produces voice-over and video clips
- Stitches clips and audio into final cut

Shared services:

- LLM provider (OpenAI, Anthropic, Azure OpenAI)
- TTS provider (ElevenLabs, Azure Speech, OpenAI Audio)
- Video generation provider (Runway, Pika, Luma, etc.)
- Storage (local, S3, Azure Blob)
- Database for state and job metadata (SQLite/Postgres)

---

## 3) Prerequisites

- Python 3.10+
- API keys for your chosen LLM/TTS/video providers
- Basic familiarity with async Python

Install core dependencies:

```bash
pip install langgraph langchain langchain-openai pydantic python-dotenv
```

Optional (recommended later):

```bash
pip install fastapi uvicorn sqlalchemy tenacity loguru
```

---

## 4) Phase 1 (Simple): Minimal Script Agent

Goal: Given a movie idea, generate a complete first-draft script.

### 4.1 Define Graph State

```python
from typing import TypedDict, Optional

class ScriptState(TypedDict, total=False):
		user_prompt: str
		genre: str
		target_minutes: int
		logline: str
		outline: str
		draft_script: str
		quality_score: float
		feedback: str
		approved: bool
```

### 4.2 Nodes You Need

- `generate_logline`
- `generate_outline`
- `write_script`
- `evaluate_script`
- `revise_script`

### 4.3 Basic Flow

```text
START -> generate_logline -> generate_outline -> write_script -> evaluate_script
evaluate_script --(score < threshold)--> revise_script -> evaluate_script
evaluate_script --(score >= threshold)--> END
```

### 4.4 Quality Gate Strategy

Use a rubric scorer node for:

- Plot coherence
- Character consistency
- Pacing
- Dialogue naturalness

If average score < 8.0, loop revision.

---

## 5) Phase 2 (Intermediate): Human Approval + Script Lock

Goal: Add safe control before spending video-generation cost.

Add a node:

- `request_human_approval`

Flow:

```text
... -> evaluate_script -> request_human_approval
request_human_approval --(approved)--> END
request_human_approval --(changes_requested)--> revise_script -> evaluate_script
```

Implementation tips:

- Persist state after every node (checkpointing)
- Save script versions (`v1`, `v2`, `final`)
- Store user feedback with timestamps

---

## 6) Phase 3 (Intermediate+): Movie Production Graph

Goal: Transform approved script into fully rendered movie.

### 6.1 Production State

```python
from typing import TypedDict, List, Dict

class ProductionState(TypedDict, total=False):
		script_id: str
		locked_script: str
		scenes: List[Dict]
		shot_list: List[Dict]
		storyboard_prompts: List[str]
		narration_chunks: List[str]
		voiceover_files: List[str]
		video_clips: List[str]
		music_file: str
		final_movie_file: str
		failed_shots: List[Dict]
```

### 6.2 Nodes

- `parse_script_to_scenes`
- `create_shot_list`
- `generate_storyboard_prompts`
- `generate_voiceover`
- `generate_video_clips`
- `assemble_timeline`
- `render_final_movie`
- `qa_final_output`

### 6.3 Flow Pattern

```text
START -> parse_script_to_scenes -> create_shot_list -> generate_storyboard_prompts
-> generate_voiceover -> generate_video_clips -> assemble_timeline -> render_final_movie -> qa_final_output -> END
```

### 6.4 Retries and Fallbacks

For expensive steps (TTS/video):

- Retry with exponential backoff
- Fallback to alternate provider/model
- Mark failed shots for selective regeneration

---

## 7) Phase 4 (Advanced): Multi-Agent Orchestration

Move from single pipeline to role-based agents:

- **Director Agent**: artistic decisions, shot style consistency
- **Writer Agent**: dialogue and scene quality
- **Cinematographer Agent**: camera language and shot prompts
- **Editor Agent**: pacing, transitions, continuity
- **Producer Agent**: budget/cost/time constraints

Use a supervisor graph that routes tasks to specialized subgraphs.

Routing examples:

- If story quality fails -> Writer Agent
- If visual mismatch fails -> Cinematographer Agent
- If runtime exceeds target -> Editor Agent

---

## 8) Suggested Project Structure

```text
project/
	app/
		graphs/
			script_graph.py
			production_graph.py
			supervisor_graph.py
		nodes/
			script_nodes.py
			production_nodes.py
			qa_nodes.py
		services/
			llm_service.py
			tts_service.py
			video_service.py
			storage_service.py
		schemas/
			state.py
			prompts.py
		api/
			main.py
			routes.py
	data/
		scripts/
		audio/
		video/
		renders/
	tests/
		test_script_graph.py
		test_production_graph.py
	.env
	requirements.txt
```

---

## 9) Example LangGraph Skeleton (Script Graph)

```python
from langgraph.graph import StateGraph, START, END

def route_after_eval(state):
		if state.get("quality_score", 0) >= 8.0:
				return "approved"
		return "needs_revision"

builder = StateGraph(ScriptState)

builder.add_node("generate_logline", generate_logline)
builder.add_node("generate_outline", generate_outline)
builder.add_node("write_script", write_script)
builder.add_node("evaluate_script", evaluate_script)
builder.add_node("revise_script", revise_script)

builder.add_edge(START, "generate_logline")
builder.add_edge("generate_logline", "generate_outline")
builder.add_edge("generate_outline", "write_script")
builder.add_edge("write_script", "evaluate_script")

builder.add_conditional_edges(
		"evaluate_script",
		route_after_eval,
		{
				"approved": END,
				"needs_revision": "revise_script"
		}
)

builder.add_edge("revise_script", "evaluate_script")

script_graph = builder.compile()
```

---

## 10) Prompting Pattern That Works

For each generation node, enforce structured output:

- Required JSON schema
- Hard constraints (genre, runtime, rating)
- Negative constraints (no plot holes, no character name drift)

Example instruction block:

```text
You are a professional screenwriter.
Return ONLY valid JSON matching this schema:
{ "scene_id": str, "summary": str, "dialogue": [ ... ] }
Constraints:
- Keep tone consistent with: neo-noir
- Scene duration between 45 and 90 seconds
- Maintain continuity from previous scene state
```

---

## 11) Data Contracts (Critical)

Define strict schemas with Pydantic for:

- Scene
- Shot
- Voice segment
- Render job

Why: It prevents invalid outputs from breaking downstream nodes.

---

## 12) Observability and Cost Control

Track per-node:

- Input/output token usage
- Latency
- Provider cost estimate
- Retry count

Set budget safeguards:

- Max script revisions
- Max shots per scene
- Max video generation retries per shot

---

## 13) Testing Strategy

Minimum test layers:

1. Unit tests for each node (schema + edge cases)
2. Graph routing tests (conditional edges)
3. Integration tests with mocked provider APIs
4. Golden tests for script quality snapshots

Critical test cases:

- Empty/ambiguous user prompt
- Provider timeout or malformed response
- Inconsistent character name across scenes
- Partial render failure and resume

---

## 14) Deployment Path

Simple to advanced rollout:

1. Local CLI: run one idea to final movie
2. FastAPI service: async job endpoints
3. Queue worker: background rendering (Celery/RQ)
4. Cloud deployment with object storage + DB
5. Monitoring and alerting dashboards

---

## 15) First 7-Day Build Plan

Day 1:
- Create state schemas and script graph skeleton

Day 2:
- Implement script generation nodes + evaluator loop

Day 3:
- Add human approval UI/API and script locking

Day 4:
- Implement scene parser and shot list generator

Day 5:
- Integrate TTS and one video provider

Day 6:
- Build assembly/render pipeline and QA checks

Day 7:
- Add retries, checkpoint resume, and tests

---

## 16) Common Pitfalls

- No schema validation between nodes
- No checkpointing before expensive steps
- Prompt instructions not strict enough
- Trying full multi-agent architecture too early
- No human approval gate before video generation

---

## 17) Next Practical Step

Start by implementing only this MVP chain:

**Idea -> Logline -> Outline -> Script -> Evaluate -> Human Approve**

Once stable, add:

**Script -> Shot List -> Voice + Video -> Assemble -> Render**

This staged approach gives fast feedback and prevents wasted compute spend.

---

## 18) Starter Codebase Quickstart

This repository now includes a runnable MVP starter implementation:

- Graphs: `app/graphs/`
- Node stubs: `app/nodes/`
- Schemas: `app/schemas/`
- Services stubs: `app/services/`
- CLI entrypoint: `app/cli.py`

Install dependencies:

```bash
pip install -r requirements.txt
```

Run script flow only:

```bash
python -m app.cli script --prompt "A detective decodes messages hidden in movie frames"
```

Run movie flow only (from a saved script file):

```bash
python -m app.cli movie --script-file data/scripts/your_script.txt
```

Run full pipeline (script -> movie):

```bash
python -m app.cli full --prompt "A young editor discovers a hidden signal inside old film reels" --json
```

Generated artifacts are written under:

- `data/scripts/`
- `data/renders/`

