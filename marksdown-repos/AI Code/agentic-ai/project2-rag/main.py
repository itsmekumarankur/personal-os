import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from agent import run_agent
from rag import index


@asynccontextmanager
async def lifespan(app: FastAPI):
    index.build(os.environ.get("DOCS_DIR", "docs"))
    print(f"Indexed {len(index.chunks)} chunks")
    yield


app = FastAPI(title="Agentic AI — Project 2: RAG Agent", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    sources: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "chunks": len(index.chunks)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    reply, sources = run_agent(req.message)
    return ChatResponse(reply=reply, sources=sources)
