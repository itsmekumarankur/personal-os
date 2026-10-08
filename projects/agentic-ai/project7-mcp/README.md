# Project 7: MCP tool integration

In Project 1 the tools were written inside the agent. Here the tools live in a separate **MCP
server**, and the agent **discovers** them at start-up through the standard protocol.

```
                      MCP (standard protocol, here over stdio)
 +---------------------+  list_tools()   +--------------------------+
 |  AGENT (MCP client) | --------------> |  MCP SERVER (server.py)  |
 |  mcp_agent.py       | <-------------- |   calculate_emi          |
 |                     |  tool list      |   get_account_summary    |
 |   Claude <-> loop   |  call_tool()    |   list_transactions      |
 |                     | --------------> |   resource policy://fees |
 +---------------------+  <-- result --  +--------------------------+
```

**Why bother.** Add a tool to the server and every agent that connects sees it, with no change
to the agent. One server can serve many agents, and tools written by others (a database, GitHub,
Slack) plug in the same way.

## Where this comes from

- **MCP Python SDK** (`pip install mcp`): https://github.com/modelcontextprotocol/python-sdk
  `FastMCP` and the `@mcp.tool()` / `@mcp.resource()` decorators in `server.py`;
  `stdio_client` and `ClientSession` in `main.py` and `cli.py`.
- **MCP docs, "Build an MCP client"**: https://modelcontextprotocol.io
  The agent flow in `mcp_agent.py`: list the server's tools, give them to Claude, forward each
  `tool_use` to `session.call_tool()`, return the `tool_result`.
- The tool-use loop itself is the one from Project 1 (Anthropic tool use docs).

Written for this project (not from those sources): the allowlist, the step limit, the result
size limit, errors sent back as errors, the sample bank logic, the tests, the FastAPI service
that keeps one MCP session open, and the Terraform.

**Version note.** The `mcp` package has a 2.x release in which `FastMCP` was renamed and other
APIs changed. This project is written for 1.x and pins `mcp==1.12.4`. Do not loosen the pin until
you are ready to port it.

## Files

| File | Purpose |
|---|---|
| `bank.py` | The business logic: EMI maths, sample accounts. No MCP, no AI. |
| `server.py` | The MCP server: 3 tools and 1 resource. |
| `mcp_agent.py` | The MCP client agent: discovery, conversion, loop, allowlist. Start here. |
| `main.py` | FastAPI: `/health`, `/tools`, `/chat`. Starts the server as a child process. |
| `cli.py` | `tools`, `call`, `resource` (no API key) and `ask` (needs a key) |
| `tests/test_mcp.py` | 23 tests: real MCP protocol in memory, a real stdio child process, fake model |
| `Dockerfile`, `infra/main.tf` | Container and AWS ECS Fargate + load balancer |

## 1. Run the tests (no API key)

```
pip install -r requirements-dev.txt
python -m pytest -q
```

## 2. Explore the server without any AI

```
python cli.py tools
python cli.py call calculate_emi '{"principal": 500000, "annual_rate_percent": 10, "months": 60}'
python cli.py call get_account_summary '{"account_id": "bad"}'      # an error, as the model would see it
python cli.py resource policy://fees
```

(Lines that say "Processing request..." are the server's log on stderr. They are normal.)
This is the best way to see what MCP is: the model is not involved at all.

## 3. Run with the model

```
export ANTHROPIC_API_KEY=your_anthropic_key
python cli.py ask "What is the EMI on 5 lakh at 10% for 5 years, and what is the balance of A-1001?"

uvicorn main:app --reload --port 8000
curl http://localhost:8000/tools
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "Show the last 3 transactions of A-1001"}'
```

Settings (environment variables): `MODEL` (default `claude-sonnet-4-5`), `ALLOWED_TOOLS`
(comma separated; if set, the agent offers and runs only those tools).

Try the allowlist: `ALLOWED_TOOLS=calculate_emi python cli.py ask "balance of A-1001?"`.
The model is never shown the account tool, so it should say it cannot help.

## 4. What to take care of (architect notes)

- **An MCP server is code you run, and its tool descriptions go into the model's prompt.**
  A server you do not control can put instructions in a description or a result. Use servers you
  trust, use the allowlist, and treat every tool result as data. The system prompt says so.
- **Least privilege.** Offer the model only the tools the job needs. Anything that moves money or
  changes data should be a separate tool with its own approval step (Project 10).
- **The model's tool call is a request, not a command.** The agent checks the name against what
  was offered before forwarding. Real servers must also validate their own inputs, as `bank.py` does.
- **The child process gets a small environment.** The MCP SDK passes only a short list (`PATH`,
  `HOME`, ...) to the stdio server, so `ANTHROPIC_API_KEY` is not passed. A test checks this.
  If a server needs a secret, pass it explicitly and only that one.
- **Never `print()` in a stdio server.** stdout carries the protocol. Log to stderr.
- **stdio means "same machine, one client".** Here the server runs inside the same container as
  the agent. To share one server between services you move to the HTTP transport; `mcp_agent.py`
  does not change, only how the session is opened.
- **Limits.** At most 6 model turns per chat and 4000 characters per tool result, so a loop or a
  huge result cannot run up cost.
- Run `uvicorn` with one worker. Each worker would start its own server process.

## 5. Docker

```
docker build -t agentic-mcp:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_anthropic_key agentic-mcp:latest
```

## 6. Deploy to AWS (ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-mcp --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-mcp:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-mcp:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-mcp:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-mcp/anthropic-key --secret-string 'your_anthropic_key'

cd infra
terraform init
terraform plan
terraform apply
```

Terraform prints `app_url`. Wait 2 to 3 minutes for the target to turn healthy; if it does not,
read CloudWatch log group `/ecs/agentic-mcp`. There is no login and only HTTP, and the sample
data is made up, so do not put real account data behind this. Run `terraform destroy` when you
finish; delete the secret and the ECR repository separately.

## Exercises

1. Add a tool `get_branch_hours(city)` in `server.py` only. Restart and run `python cli.py tools`. The agent now has it; you changed no agent code.
2. Remove a tool's docstring and ask a question that needs it. Does the model still pick it? (Descriptions are the interface.)
3. Set `ALLOWED_TOOLS` to two tools and ask for the third. Read the answer.
4. Make `list_transactions` return 100 rows and look at what `[truncated]` does.
5. Read `policy://fees` from the agent: add a `read_resource` step and think about when a resource is better than a tool.
