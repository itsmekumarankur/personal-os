"""FastAPI service. On startup it launches the MCP server as a child process (stdio) and keeps one
session open for all requests. In a bigger system the server would run on its own and be reached over
HTTP; the agent code in mcp_agent.py would not change."""
import sys
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from anthropic import APIError
from fastapi import FastAPI, HTTPException, Request
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field

import mcp_agent

SERVER_PATH = str(Path(__file__).with_name("server.py"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        params = StdioServerParameters(command=sys.executable, args=[SERVER_PATH])
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        app.state.session = session
        yield


app = FastAPI(title="Agentic AI — Project 7: MCP tools", lifespan=lifespan)

# Tests replace this. Resolved at call time.
model_call = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ToolCall(BaseModel):
    name: str
    input: dict
    is_error: bool


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCall]
    turns: int
    truncated: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tools")
async def tools(request: Request):
    """What the agent can use right now. These come from the MCP server, not from this code."""
    found = await mcp_agent.list_tools(request.app.state.session, mcp_agent.allowed_names())
    return [{"name": t["name"], "description": t["description"]} for t in found]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    try:
        return await mcp_agent.run_agent(
            request.app.state.session, req.message,
            model_call=model_call, allowed=mcp_agent.allowed_names(),
        )
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"Model API error: {e}")
