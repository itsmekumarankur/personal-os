from anthropic import APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from review import REVIEWERS, AllReviewersFailed, review_design
from vote import vote

app = FastAPI(title="Agentic AI — Project 5: Parallelization")


# ---------------------------------------------------------
# Request coming to /review API
# Simply: "Here is my design, please review it."
# ---------------------------------------------------------
class ReviewRequest(BaseModel):
    design: str = Field(min_length=1, max_length=20000)

    # Optional list of reviewers.
    # If not given, all reviewers will be used.
    reviewers: list[str] | None = Field(
        default=None,
        description="Subset of /reviewers; default is all"
    )


# ---------------------------------------------------------
# One reviewer's result
# Simply: Stores what one reviewer said about the design.
# ---------------------------------------------------------
class ReviewItem(BaseModel):
    reviewer: str       # Name of the reviewer
    ok: bool             # Did the reviewer complete successfully?
    error: str | None    # Error message, if something failed
    findings: str        # What problems did the reviewer find?
    verdict: str         # Reviewer's final opinion
    high_count: int      # Number of high-severity issues found


# ---------------------------------------------------------
# Final response from /review API
# Simply: Combines results from all reviewers.
# ---------------------------------------------------------
class ReviewResponse(BaseModel):
    verdict: str                 # Overall final decision
    complete: bool               # Did all required reviews complete?
    summary: str                 # Short summary of all reviews
    reviews: list[ReviewItem]    # Individual reviewer results
    timing: dict[str, float]     # How much time each step took


# ---------------------------------------------------------
# Request coming to /vote API
# Simply: "Give me some text and a question,
#          and let multiple AI voters decide."
# ---------------------------------------------------------
class VoteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    question: str = Field(min_length=1, max_length=500)

    # Number of AI voters.
    # Must be between 3 and 9.
    votes: int = Field(default=5, ge=3, le=9)

    # -----------------------------------------------------
    # Check that number of voters is ODD.
    # Example: 5 voters -> majority can be 3 vs 2.
    # -----------------------------------------------------
    @field_validator("votes")
    @classmethod
    def odd(cls, v: int) -> int:
        if v % 2 == 0:
            raise ValueError("votes must be odd so a majority is possible")
        return v


# ---------------------------------------------------------
# Health check API
# Simply: "Is my application running?"
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------
# Get available reviewers
# Simply: Returns the list of reviewers we can use.
# ---------------------------------------------------------
@app.get("/reviewers")
def reviewers():
    return REVIEWERS


# ---------------------------------------------------------
# Design review API
# Simply:
# User sends a design
#       ↓
# Multiple reviewers review it
#       ↓
# We return the combined result
# ---------------------------------------------------------
@app.post("/review", response_model=ReviewResponse)
def review(req: ReviewRequest):
    try:
        return review_design(req.design, req.reviewers)

    # User sent invalid input
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Reviewers/model failed
    except (AllReviewersFailed, APIError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Model API error: {e}"
        )


# ---------------------------------------------------------
# Voting API
# Simply:
# Send text + question
#       ↓
# Multiple AI voters vote
#       ↓
# Return the final decision
# ---------------------------------------------------------
@app.post("/vote")
def vote_endpoint(req: VoteRequest):
    try:
        return vote(req.text, req.question, req.votes)

    # Something went wrong while calling the AI/model
    except (RuntimeError, APIError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"Model API error: {e}"
        )