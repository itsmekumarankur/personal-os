from anthropic import APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from orchestrator import HARD_MAX_TASKS, AllWorkersFailed, orchestrate

app = FastAPI(title="Agentic AI — Project 6: Orchestrator-Workers")


class OrchestrateRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=8000)
    max_tasks: int = Field(default=4, ge=1, le=HARD_MAX_TASKS, description="Upper limit on subtasks")


class TaskResult(BaseModel):
    id: int
    title: str
    description: str
    ok: bool
    error: str | None
    result: str
    seconds: float


class OrchestrateResponse(BaseModel):
    analysis: str
    truncated: bool
    fallback: bool
    complete: bool
    tasks: list[TaskResult]
    final: str
    timing: dict[str, float]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orchestrate", response_model=OrchestrateResponse)
def orchestrate_endpoint(req: OrchestrateRequest):
    try:
        return orchestrate(req.goal, req.max_tasks)
    except (AllWorkersFailed, APIError) as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")
