"""Command-line client for the stdio MCP server."""

import argparse
import asyncio
from pathlib import Path
from typing import Any

from fastmcp import Client


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Call the stdio example MCP server.")
    parser.add_argument(
        "--server",
        type=Path,
        default=Path("server.py"),
        help="Path to the MCP server script (default: server.py).",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list-tools", help="List the tools exposed by the server.")

    add_parser = commands.add_parser("add", help="Add two numbers.")
    add_parser.add_argument("a", type=int)
    add_parser.add_argument("b", type=int)

    greet_parser = commands.add_parser("greet", help="Greet someone.")
    greet_parser.add_argument("name")

    return parser


def format_result(result: Any) -> str:
    """Return a readable representation of an MCP tool result."""
    if getattr(result, "data", None) is not None:
        return str(result.data)

    content = getattr(result, "content", None)
    if content:
        return "\n".join(
            str(getattr(item, "text", item))
            for item in content
        )

    return str(result)


async def run_client(args: argparse.Namespace) -> None:
    """Connect to the server and execute the requested command."""
    async with Client(args.server) as client:
        if args.command == "list-tools":
            tools = await client.list_tools()
            for tool in tools:
                print(f"{tool.name}: {tool.description or 'No description'}")
            return

        if args.command == "add":
            result = await client.call_tool("add_numbers", {"a": args.a, "b": args.b})
        else:
            result = await client.call_tool("greet", {"name": args.name})

        print(format_result(result))


def main() -> None:
    """Parse arguments and run the MCP client."""
    asyncio.run(run_client(build_parser().parse_args()))


if __name__ == "__main__":
    main()