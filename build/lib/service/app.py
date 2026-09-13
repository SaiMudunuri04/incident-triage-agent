"""Read-only incident triage API."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agents import ReadOnlyTools, run_incident
from .llm import ChatClient

app = FastAPI(title="Incident triage agent", version="0.1.0")


class Incident(BaseModel):
    description: str = Field(min_length=5, max_length=2000)
    max_steps: int = Field(default=6, ge=1, le=12)


def tools() -> ReadOnlyTools:
    root = Path(os.getenv("RUNBOOK_ROOT", "/data/runbooks"))
    metrics_path = Path(os.getenv("METRICS_PATH", "/data/metrics.json"))
    if not root.is_dir() or not metrics_path.is_file():
        raise FileNotFoundError("Runbooks or metrics unavailable")
    runbooks = {p.stem: p.read_text(encoding="utf-8") for p in root.glob("*.md") if p.is_file()}
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if not runbooks or not isinstance(metrics, dict):
        raise ValueError("Invalid tool data")
    return ReadOnlyTools(runbooks, metrics)


@app.get("/health/live")
def live():
    return {"status": "alive"}


@app.get("/health/ready")
def ready():
    try:
        tools()
    except (FileNotFoundError, ValueError):
        raise HTTPException(503, "Tool data unavailable")
    return {"status": "ready"}


@app.post("/triage")
def triage(request: Incident):
    try:
        available = tools()
    except (FileNotFoundError, ValueError):
        raise HTTPException(503, "Tool data unavailable")
    base_url, model = os.getenv("LLM_BASE_URL"), os.getenv("LLM_MODEL")
    if not base_url or not model:
        raise HTTPException(503, "Inference endpoint unavailable")
    return run_incident(request.description, ChatClient(base_url, model), available, request.max_steps)
