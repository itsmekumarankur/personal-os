from fastmcp import FastMCP, Context
from pydantic import BaseModel

mcp = FastMCP("WeatherOrchestrator")

# --- 1. Base Tools (The "Conflicting" Sources) ---
@mcp.tool()
def get_sensor_weather(location: str) -> str:
    """Gets raw data from local hardware sensors."""
    return f"Sensor at {location}: 22°C, Heavy Rain, Humidity 90%"

@mcp.tool()
def get_satellite_weather(location: str) -> str:
    """Gets high-altitude satellite imaging data."""
    return f"Satellite over {location}: 25°C, Sunny, Humidity 20%"

# --- 2. The Orchestrator Tool (Context Flow & Decision Making) ---
@mcp.tool()
async def resolve_weather_report(location: str, ctx: Context) -> str:
    """
    Orchestrates multiple tools and uses the LLM to decide which 
    result is more credible based on context.
    """
    # Step 1: Gather data from conflicting tools
    sensor_data = get_sensor_weather(location)
    satellite_data = get_satellite_weather(location)

    # Step 2: Sampling - Let the LLM decide which is correct
    # We pass the tools themselves so the LLM can "see" their descriptions
    await ctx.log("Initiating Model-side decision making...", level="info")
    
    prompt = f"""
    I have two conflicting reports for {location}:
    1. {sensor_data}
    2. {satellite_data}
    
    As an expert meteorologist, analyze these. Hint: Hardware sensors are 
    often more accurate for current rain, while satellites are better for temperature.
    Provide a unified, final verdict.
    """

    # The 'sample' call sends this back to the client's LLM
    decision = await ctx.sample(
        messages=prompt,
        system_prompt="You are a decision-making agent inside an MCP server.",
        model_preferences=["claude-3-5-sonnet", "gpt-4o"]
    )

    return f"--- FINAL RESOLUTION ---\n{decision.text}"

if __name__ == "__main__":
    # Streamable HTTP is the 2026 transport standard
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)