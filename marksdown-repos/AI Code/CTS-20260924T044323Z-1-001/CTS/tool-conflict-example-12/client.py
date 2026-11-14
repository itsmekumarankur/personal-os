import asyncio
import mcp.types
from fastmcp import Client
from fastmcp.client.sampling import SamplingHandler

# Simple sampling handler (echo / placeholder). Replace with real LLM call.
async def sampling_handler(messages, params, context) -> str:
    return "[LLM DECISION] Based on the sensor and satellite data, the most credible report is: Sensor at Bangalore: 22°C, Heavy Rain, Humidity 90%. The satellite likely missed the current rain conditions. Final Verdict: It's currently raining in Bangalore with high humidity."

async def main():
    async with Client(
        "http://127.0.0.1:8000/mcp",
        sampling_handler=sampling_handler,
        sampling_capabilities=mcp.types.SamplingCapability(),  # optional but explicit
    ) as client:
        print("🚀 Connected to Orchestrator (Sampling Enabled)")
        result = await client.call_tool(
            "resolve_weather_report", arguments={"location": "Bangalore"}
        )
        print(f"\n{result}")

if __name__ == "__main__":
    asyncio.run(main())