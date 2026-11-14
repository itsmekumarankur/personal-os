"""Calling the remote MCP server with the official SDK client, a bearer token, and tool pinning."""
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from tool_pinning import PinMismatch, ToolPins


class ToolFailed(Exception):
    pass


class RemoteMCP:
    def __init__(self, url: str, get_token, pins: ToolPins | None = None, traceparent: str | None = None):
        """get_token() -> a bearer token string (so the caller decides: own token, or exchanged token)."""
        self.url, self.get_token, self.pins, self.traceparent = url, get_token, pins, traceparent

    def _headers(self) -> dict:
        h = {"Authorization": f"Bearer {self.get_token()}"}
        if self.traceparent:
            h["traceparent"] = self.traceparent
        return h

    async def _session_run(self, fn):
        async with streamablehttp_client(self.url, headers=self._headers()) as (r, w, _):
            async with ClientSession(r, w) as s:
                await s.initialize()
                return await fn(s)

    async def list_tools(self) -> list:
        async def fn(s):
            tools = [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in (await s.list_tools()).tools]
            try:
                return self.pins.check_or_trust(tools) if self.pins else tools
            except PinMismatch as e:
                return e                                     # returned, not raised: an exception inside the session is wrapped by anyio
        out = await self._session_run(fn)
        if isinstance(out, PinMismatch):
            raise out
        return out

    async def call_tool_blocks(self, name: str, args: dict) -> list:
        """One string per content block. (FastMCP returns a list result as ONE BLOCK PER ITEM, so a list is not one JSON document.)"""
        async def fn(s):
            if self.pins:                                    # check the tool list BEFORE the call is made
                try:
                    self.pins.check_or_trust([{"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                                              for t in (await s.list_tools()).tools])
                except PinMismatch as e:
                    return e, False
            res = await s.call_tool(name, args)
            return [getattr(c, "text", "") for c in res.content], bool(res.isError)
        blocks, failed = await self._session_run(fn)
        if isinstance(blocks, PinMismatch):
            raise blocks
        # raise AFTER the session closed, so callers see ToolFailed, not an ExceptionGroup
        if failed:
            raise ToolFailed(" ".join(blocks))
        return blocks

    async def call_tool(self, name: str, args: dict) -> str:
        return "".join(await self.call_tool_blocks(name, args))

    def call_tool_sync(self, name: str, args: dict) -> str:
        return asyncio.run(self.call_tool(name, args))
