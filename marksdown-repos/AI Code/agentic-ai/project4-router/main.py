from anthropic import APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from router import HUMAN, HUMAN_DESCRIPTION, ROUTES, route_ticket

app = FastAPI(title="Agentic AI — Project 4: Routing")


class TriageRequest(BaseModel):
    ticket: str = Field(min_length=1, max_length=4000)


class TriageResponse(BaseModel):
    route: str
    reasoning: str
    reply: str
    escalated: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/routes")
def routes():
    items = {name: r.description for name, r in ROUTES.items()}
    items[HUMAN] = HUMAN_DESCRIPTION
    return items


@app.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest):
    try:
        return route_ticket(req.ticket)
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")
