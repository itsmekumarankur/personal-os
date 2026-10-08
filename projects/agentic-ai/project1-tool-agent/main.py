# FastAPI is used to expose our AI Agent as an HTTP API.
# BaseModel is used to define/validate the request and response structure.
# run_agent() is our actual AI agent logic from agent.py.


from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(title="Agentic AI — Project 1")

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
    reply = run_agent(req.message)
    return ChatResponse(reply=reply)