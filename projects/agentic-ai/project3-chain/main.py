from anthropic import APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from chain import run_pipeline

app = FastAPI(title="Agentic AI — Project 3: Prompt Chaining")


class WriteRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000, description="What to write")
    audience: str = Field(default="a general reader", max_length=200)
    max_words: int = Field(default=200, ge=50, le=1000)


class WriteResponse(BaseModel):
    final: str
    draft: str
    critique: str
    verdict: str
    steps_run: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/write", response_model=WriteResponse)
def write(req: WriteRequest):
    try:
        return run_pipeline(req.task, req.audience, req.max_words)
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")
