from anthropic import APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from review import REVIEWERS, AllReviewersFailed, review_design
from vote import vote

app = FastAPI(title="Agentic AI — Project 5: Parallelization")


class ReviewRequest(BaseModel):
    design: str = Field(min_length=1, max_length=20000)
    reviewers: list[str] | None = Field(default=None, description="Subset of /reviewers; default is all")


class ReviewItem(BaseModel):
    reviewer: str
    ok: bool
    error: str | None
    findings: str
    verdict: str
    high_count: int


class ReviewResponse(BaseModel):
    verdict: str
    complete: bool
    summary: str
    reviews: list[ReviewItem]
    timing: dict[str, float]


class VoteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    question: str = Field(min_length=1, max_length=500)
    votes: int = Field(default=5, ge=3, le=9)

    @field_validator("votes")
    @classmethod
    def odd(cls, v: int) -> int:
        if v % 2 == 0:
            raise ValueError("votes must be odd so a majority is possible")
        return v


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reviewers")
def reviewers():
    return REVIEWERS


@app.post("/review", response_model=ReviewResponse)
def review(req: ReviewRequest):
    try:
        return review_design(req.design, req.reviewers)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (AllReviewersFailed, APIError) as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")


@app.post("/vote")
def vote_endpoint(req: VoteRequest):
    try:
        return vote(req.text, req.question, req.votes)
    except (RuntimeError, APIError) as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")
