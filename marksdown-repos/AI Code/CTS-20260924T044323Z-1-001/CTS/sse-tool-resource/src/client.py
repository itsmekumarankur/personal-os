import asyncio
from fastmcp import Client

async def main() :
    async with Client("http://127.0.0.1:8000/sse") as client:

        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"{tool.name}: {tool.description or 'No description'}")

        # Call the calculate_growth_rate tool
        growth_rate_result = await client.call_tool(
            "calculate_growth_rate", {"initial_value": 1000, "rate": 0.05, "time": 10}
        )   

        print(f"Growth Rate Result: {growth_rate_result.data}")

        #List the resources
        resources = await client.list_resources()
        print("Available resources:")
        for resource in resources:
            print(f"{resource.name}: {resource.description or 'No description'}")

        # Call the get_status resource
        status_result = await client.read_resource("config://status")
        print(f"Status Result: {status_result}")


if __name__ == "__main__":
    asyncio.run(main())

    