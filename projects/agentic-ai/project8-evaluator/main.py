from typing import Annotated

from anthropic import APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from refine import DEFAULT_CRITERIA, GenerationError, refine

app = FastAPI(title="Agentic AI — Project 8: Evaluator-Optimizer")


class RefineRequest(BaseModel):
    task: str = Field(min_length=1, max_length=6000, description="The brief: what to write, with the facts")
    criteria: list[Annotated[str, Field(min_length=1, max_length=200)]] | None = Field(
        default=None, max_length=8, description="What the text must satisfy. Default: incident-update rubric")
    max_words: int = Field(default=150, ge=30, le=500)
    max_rounds: int = Field(default=3, ge=1, le=5, description="Each round is up to 2 model calls")


class Round(BaseModel):
    round: int
    text: str
    words: int
    verdict: str
    feedback: str
    checked_by: str


class RefineResponse(BaseModel):
    final: str
    passed: bool
    status: str
    rounds: int
    llm_calls: int
    history: list[Round]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/criteria")
def criteria():
    return DEFAULT_CRITERIA


@app.post("/refine", response_model=RefineResponse)
def refine_endpoint(req: RefineRequest):
    try:
        return refine(req.task, req.criteria, req.max_words, req.max_rounds)
    except (GenerationError, APIError) as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")
