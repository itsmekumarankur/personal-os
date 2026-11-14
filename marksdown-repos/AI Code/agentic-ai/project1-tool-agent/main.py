# FastAPI is used to expose our AI Agent as an HTTP API.
# BaseModel is used to define/validate the request and response structure.
# run_agent() is our actual AI agent logic from agent.py.


import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from agent import run_agent

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

app = FastAPI(title="Agentic AI — Project 1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": str(exc)})

# Defines what the client should send to /chat.
class ChatRequest(BaseModel):
    message: str

# Defines the structure of the response from /chat.
class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {"status": "ok"}


# Main endpoint for interacting with our AI Agent.
#
# POST /chat
#
# Flow:
#
# Client
#   |
#   | POST /chat
#   | {"message": "..."}
#   v
# FastAPI
#   |
#   v
# run_agent()
#   |
#   v
# Claude + Tool Calling
#   |
#   v
# Agent Response
#   |
#   v
# {"reply": "..."}
#

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    logger.info("Received message: %s", req.message)
    reply = run_agent(req.message)
    logger.info("Agent reply: %s", reply)
    return ChatResponse(reply=reply)


