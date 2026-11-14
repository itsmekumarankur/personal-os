"""An MCP server: the same tools, but offered over the standard protocol.

Adapted from the official MCP Python SDK (FastMCP, pip package "mcp"):
https://github.com/modelcontextprotocol/python-sdk
The decorators @mcp.tool() and @mcp.resource() turn a normal function into a tool or a
resource. The function's name, type hints and docstring become the description that the
model reads, so write them as if for a new colleague.

Run alone (waits for a client on stdin/stdout):   python server.py

IMPORTANT for the stdio transport: stdout is the protocol channel. Never print() to it.
Anything you want to log goes to stderr.
"""
from mcp.server.fastmcp import FastMCP

import bank

mcp = FastMCP("bank-tools")


@mcp.tool()
def calculate_emi(principal: float, annual_rate_percent: float, months: int) -> str:
    """Calculate the monthly loan instalment (EMI), total payable and total interest.

    principal: loan amount, more than 0.
    annual_rate_percent: yearly interest rate in percent, for example 10.5.
    months: loan length in months, 1 to 480.
    """
    return bank.as_text(bank.emi(principal, annual_rate_percent, months))


@mcp.tool()
def get_account_summary(account_id: str) -> str:
    """Get the holder name, account type, balance and currency of one account, e.g. 'A-1001'."""
    return bank.as_text(bank.account_summary(account_id))


@mcp.tool()
def list_transactions(account_id: str, limit: int = 5) -> str:
    """List the most recent transactions of one account, newest first. limit is 1 to 20.
    Positive amounts are credits, negative amounts are debits."""
    return bank.as_text(bank.transactions(account_id, limit))


@mcp.resource("policy://fees")
def fees_policy() -> str:
    """The sample fee policy text. A resource is read-only context, not an action."""
    return bank.FEES_POLICY


if __name__ == "__main__":
    mcp.run()          # stdio transport by default
