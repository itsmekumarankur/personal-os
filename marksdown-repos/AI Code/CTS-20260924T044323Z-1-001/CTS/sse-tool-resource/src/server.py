from fastmcp import FastMCP

mcp = FastMCP("ModernAgentServer")

@mcp.tool()
def calculate_growth_rate(initial_value: float, rate: float, time: float) -> float:
    """Calculate the growth rate using the formula: final_value = initial_value * (1 + rate) ** time."""
    return initial_value * (1 + rate) ** time

@mcp.tool()
def simple_interest(principal: float, rate: float, time: float) -> float:
    """Calculate simple interest using the formula: interest = principal * rate * time."""
    return principal * rate * time

@mcp.resource("config://status")
def get_status() -> str:
    """Return the current status of the server."""
    return "Server is running and ready to accept requests. : 2026 - Agentic-standard"

# create 3 prompts
@mcp.prompt("growth_rate_prompt")
def growth_rate_prompt(initial_value: float, rate: float, time: float) -> str:
    return f"Calculate the growth rate for an initial value of {initial_value}, a rate of {rate}, and a time period of {time}."

@mcp.prompt("simple_interest_prompt")
def simple_interest_prompt(principal: float, rate: float, time: float) -> str:
    return f"Calculate the simple interest for a principal of {principal}, a rate of {rate}, and a time period of {time}."

@mcp.prompt("status_prompt")
def status_prompt() -> str:
    return "What is the current status of the server?"



if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)

