"""Talk to the MCP server from the terminal.

    python cli.py tools                          list what the server offers (no API key needed)
    python cli.py call calculate_emi '{"principal": 500000, "annual_rate_percent": 10, "months": 60}'
                                                 call one tool directly (no API key needed)
    python cli.py resource policy://fees         read a resource (no API key needed)
    python cli.py ask "What is the EMI on 5 lakh at 10% for 5 years?"      (needs ANTHROPIC_API_KEY)
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import mcp_agent

SERVER = str(Path(__file__).with_name("server.py"))


async def main(argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return
    params = StdioServerParameters(command=sys.executable, args=[SERVER])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            cmd = argv[0]
            if cmd == "tools":
                for t in (await session.list_tools()).tools:
                    print(f"{t.name}\n  {(t.description or '').splitlines()[0]}\n  inputs: {json.dumps(t.inputSchema.get('properties', {}))}\n")
            elif cmd == "call":
                out = await session.call_tool(argv[1], json.loads(argv[2]) if len(argv) > 2 else {})
                print(("ERROR: " if out.isError else "") + "\n".join(c.text for c in out.content))
            elif cmd == "resource":
                res = await session.read_resource(argv[1])
                print("\n".join(getattr(c, "text", "") for c in res.contents))
            elif cmd == "ask":
                r = await mcp_agent.run_agent(session, argv[1], allowed=mcp_agent.allowed_names())
                for c in r["tool_calls"]:
                    print(f"[tool] {c['name']} {json.dumps(c['input'])}{'  (error)' if c['is_error'] else ''}")
                print(r["reply"])
            else:
                print(__doc__)


asyncio.run(main(sys.argv[1:]))
