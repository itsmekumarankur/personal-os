import asyncio
from fastmcp import Client

async def main():
    # Connect to the streamable-http endpoint
    async with Client("http://127.0.0.1:8000/mcp") as client:
        
        # 1. Access Static Resource
        static_data = await client.read_resource("resource://config/info")
        print(f"STATIC DATA:\n{static_data}\n")

        # 2. Access Dynamic Resource
        user_id = "123"
        dynamic_data = await client.read_resource(f"data://user/{user_id}/profile")
        print(f"DYNAMIC DATA (User {user_id}):\n{dynamic_data}\n")

        # 3. Access Streaming Tool
        print("STARTING STREAMING TOOL...")
        async def handle_progress(current, total):
            print(f"Client-side Progress: {current}/{total} steps received.")

        result = await client.call_tool(
            "track_live_data", 
            arguments={"sensor_id": "Alpha-9"},
            #on_progress=handle_progress
        )
        print(f"\nFINAL TOOL RESULT: {result}")

if __name__ == "__main__":
    asyncio.run(main())