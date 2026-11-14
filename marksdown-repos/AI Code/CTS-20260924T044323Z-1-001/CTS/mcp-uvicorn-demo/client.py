# client.py
import asyncio
from fastmcp import Client

async def main():
    # Connect to the local Uvicorn-hosted MCP server
    async with Client("http://127.0.0.1:8000/sse") as client:
        print("--- Connected to MCP Server ---")
        
        # 1. List available tools
        tools = await client.list_tools()
        print(f"Available Tools: {[t.name for t in tools]}")
        
        # 2. Call the growth calculator tool
        result = await client.call_tool("calculate_growth", arguments={"initial": 1000, "rate": 0.05, "years": 10})
        print(f"Tool Result (Growth): {result}")
        
        # 3. Read the status resource
        status = await client.read_resource("config://status")
        print(f"Resource Content: {status}")

if __name__ == "__main__":
    asyncio.run(main())