# server.py
from fastmcp import FastMCP

# Initialize FastMCP with a name
mcp = FastMCP("ModernAgentServer")

# Add a simple tool for the client to call
@mcp.tool()
def calculate_growth(initial: float, rate: float, years: int) -> float:
    """Calculates compound interest growth."""
    return initial * (1 + rate) ** years

# Add a resource for the client to read
@mcp.resource("config://status")
def get_status() -> str:
    """Returns the current server status."""
    return "Server is operational. Mode: 2026-Agentic-Standard."

if __name__ == "__main__":
    # In 2026, 'mcp.run()' supports the 'sse' transport directly
    # which internally uses Uvicorn to host the HTTP server.
    mcp.run(transport="sse", host="127.0.0.1", port=8000)