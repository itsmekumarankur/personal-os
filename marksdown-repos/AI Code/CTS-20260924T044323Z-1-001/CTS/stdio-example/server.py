from fastmcp import FastMCP

mcp = FastMCP("Simple_Demo_MCP_server")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@mcp.tool()
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello Welcome to MCP Demos, {name}!"


if __name__ == "__main__":
    mcp.run(transport ="stdio")

