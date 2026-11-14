import asyncio
import json 
from datetime import datetime
from fastmcp import FastMCP, Context

mcp = FastMCP("ResourceTypesServer")

# Static Resource 
# Useful for configuration, fixed data and docs 

@mcp.resource("resource://config/info")
def get_static_config() -> str :
    """provides fixed static configuration information"""
    return "System Version 3.2.0 \n environment : production \n region: us-east-1"

# Dynamic Resource use URI templates 
@mcp.resource("data://user/{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """Simulates fetching user profile data based on user_id"""
    mock_db = {
        "123": {"name": "Alice", "role": "admin"},
        "456": {"name": "Bob", "role": "user"},
        "789": {"name": "Charlie", "role": "guest"},
    }
    user = mock_db.get(user_id, {"error" : "User not found"})
    return json.dumps(user)

# Streaming Resource via progress/ logs
@mcp.tool
async def track_live_data(sensor_id: str, ctx: Context) -> str:
    """Simulates a streaming resource that provides live data updates."""
    for i in range(1,6):
        await asyncio.sleep(1)  # Simulate delay in receiving data
        # Report progress to the client
        await ctx.report_progress(1, 5)
        await ctx.info(f"sensor {sensor_id} reading {i}: value={i*10}")
    return f"Completed tracking sensor {sensor_id}"

if __name__ == "__main__":
    mcp.run(transport = "streamable-http", host = "127.0.0.1", port = 8000)

