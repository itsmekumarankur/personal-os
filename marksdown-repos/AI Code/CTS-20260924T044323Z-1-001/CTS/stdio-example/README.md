## stdio MCP example

This project contains a FastMCP server and a command-line client for calling it.

Run the client from the project directory:

```powershell
uv run mcp-client list-tools
uv run mcp-client add 2 3
uv run mcp-client greet Ada
```

To use a different server script, pass its path before the command:

```powershell
uv run mcp-client --server path\to\server.py list-tools
```
