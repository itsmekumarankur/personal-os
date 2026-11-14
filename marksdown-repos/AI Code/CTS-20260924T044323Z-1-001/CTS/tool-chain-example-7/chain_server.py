from fastmcp import FastMCP, Context

mcp = FastMCP("ToolChainServer")

@mcp.tool
async def fetch_website(url: str) -> str:
    # import aiohttp
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(url) as response:
    #         return await response.text()

    database = {
        "google.com": "<html>Google Homepage Simulated</html>",
        "databricks.com": "<html>Databricks Homepage Simulated</html>",
    }

    return database.get(url, "<html>404 Not Found</html>")

@mcp.tool
async def summarize_research(url: str, ctx: Context) -> str:
    """ Higher level tool that calls fetch_website to get the content and then summarizes it. """
    await ctx.info(f"Chaining Request to fetch_website for URL: {url}")

    # --- tool chaining starts here ---
    # Use the server API to call the local tool. Context does not implement
    # `call_tool` directly, so call through the FastMCP instance available
    # on the context (`ctx.fastmcp`). The server returns a ToolResult object
    # — extract text blocks into a string for downstream processing.
    result = await ctx.fastmcp.call_tool("fetch_website", {"url": url})

    # Normalize ToolResult -> raw string
    try:
        content_blocks = getattr(result, "content", None)
        if content_blocks is None:
            raw_data = str(result)
        else:
            parts = []
            for block in content_blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
                else:
                    parts.append(str(block))
            raw_data = "".join(parts)
    except Exception:
        raw_data = str(result)
    # --- tool chaining ends here ---

    # Process the raw data (simulated summarization)
    summary = f"Summary of {url}: {raw_data.upper()}"

    return summary


if __name__ == "__main__":
    mcp.run()   