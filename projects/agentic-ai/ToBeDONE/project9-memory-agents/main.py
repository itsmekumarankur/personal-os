import logging
import os

from anthropic import APIError
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from agents import SessionStore, chat_turn, remember
from memory_store import MemoryStore

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Agentic AI — Project 9: Multi-agent with memory")

store = MemoryStore(os.environ.get("MEMORY_DIR", "./data/memory"))
sessions = SessionStore()

ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


class ChatRequest(BaseModel):
    user_id: str = Field(pattern=ID_PATTERN)
    session_id: str = Field(pattern=ID_PATTERN, description="A new session_id starts a fresh conversation; memory stays")
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    agents_used: list[str]
    usage: dict[str, int]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, background: BackgroundTasks):
    try:
        result = chat_turn(store, sessions, req.user_id, req.session_id, req.message)
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")
    # The archivist runs after the response has been sent, so the user does not wait for it.
    background.add_task(remember, store, req.user_id, req.message, result["reply"])
    return result


@app.get("/memory/{user_id}")
def read_memory(user_id: str):
    """Show everything stored about a user. Users should be able to see what is remembered."""
    try:
        return {"user_id": user_id, "files": store.user(user_id).files()}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.delete("/memory/{user_id}")
def forget(user_id: str):
    """Forget everything about a user: files and conversations."""
    try:
        store.user(user_id).clear()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    sessions.clear_user(user_id)
    return {"user_id": user_id, "forgotten": True}
