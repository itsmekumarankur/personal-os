# Project 9: Multi-agent with memory

An assistant that **remembers you across conversations**, built from three agents that each have
a different job and different rights, and one shared memory.

```
 you ──message──>  LEAD  ── ask_planner ──>  PLANNER
                    │  ▲                        │
        read only   │  │ <memory> in prompt     │ read only
                    ▼  │                        ▼
              ┌──────────────────────────────────────┐
              │  MEMORY FILES   (one folder per user) │ <── write ── ARCHIVIST
              │  /memories/profile.md                 │      (runs AFTER the reply,
              │  /memories/preferences.md             │       sees the exchange,
              │  /memories/projects/<name>.md         │       decides what to keep)
              └──────────────────────────────────────┘
 you <──reply── LEAD
```

**Two kinds of memory, on purpose**

| | Short-term | Long-term |
|---|---|---|
| What | the current conversation (`session_id`) | files about the user |
| Where | in the process (`SessionStore`) | on disk / EFS (`MemoryStore`) |
| Lifetime | until restart or a new `session_id` | until the user says "forget" |

**Why three agents and not one.** Each agent gets only what it needs. The lead talks to the user
and cannot write memory. The planner can only read. Only the archivist writes, and its prompt is
entirely about what is worth keeping and what must never be kept. A mistake or an attack on the
conversation therefore cannot directly edit memory.

## Where this comes from

- **Anthropic memory tool**, docs and SDK: memory is a set of files outside the conversation, read
  at the start and edited with six commands (`view`, `create`, `str_replace`, `insert`, `delete`,
  `rename`) under a `/memories` path. `memory_store.py` follows the official reference
  implementation in the Anthropic Python SDK (`BetaLocalFilesystemMemoryTool`, in
  `anthropic/lib/tools/_beta_builtin_memory_tool.py`): same commands, same path rules, same
  wording of results. Plain tool schema instead of the beta tool type, so it works with the pinned SDK.
- **Anthropic engineering post "How we built our multi-agent research system"**: a lead agent
  delegating to specialist subagents, each with its own prompt. Note: I could not open the post in
  this session, so the ideas I took from it come from my background knowledge. Read the post and
  check my summary, especially its numbers on token cost.
- The tool-use loop is the one from Project 1; XML-tag safety habits are from Projects 3 to 5.

Written for this project (not from those sources): per-user folders, the rights split between the
three agents, memory injected by code into the lead's prompt, the archivist prompt and its privacy
rules, the secret-looking-text filter, limits, session store, API, tests, and the EFS Terraform.

## Files

| File | Purpose |
|---|---|
| `memory_store.py` | The memory: six commands, path safety, limits, per-user locks. Start here. |
| `agents.py` | Lead, planner, archivist, the shared tool loop, `SessionStore` |
| `llm.py` | One place that calls Claude |
| `main.py` | FastAPI: `/chat`, `/memory/{user_id}` (see), `DELETE /memory/{user_id}` (forget), `/health` |
| `cli.py` | Chat in the terminal, show or forget memory |
| `tests/` | 49 tests with a fake model; no API key needed |
| `Dockerfile`, `infra/main.tf` | Container, and AWS ECS Fargate + load balancer + EFS for memory |

## 1. Run the tests (no API key)

```
pip install -r requirements-dev.txt
python -m pytest -q
```

The key test is `test_memory_survives_into_a_new_session_but_not_to_another_user`.

## 2. Try it

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_anthropic_key

python cli.py --user ankur                       # tell it about a project, then type: exit
python cli.py --user ankur --show                # look at what it remembered
python cli.py --user ankur --session second      # a NEW conversation: does it remember?
python cli.py --user ankur --forget

uvicorn main:app --port 8000
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"user_id": "ankur", "session_id": "monday", "message": "I am building a loan calculator in Rust. Keep answers short."}'
curl http://localhost:8000/memory/ankur
```

Settings: `MODEL` (default `claude-sonnet-4-5`; if it is not available to your account, set one you
can use), `MEMORY_DIR` (default `./data/memory`).

## 3. What to take care of (architect notes)

- **Memory is persistent prompt injection waiting to happen.** Anything saved will be read into a
  future prompt. If someone gets a hostile sentence into memory, it attacks every later session.
  Defences here: only the archivist writes; it is told the exchange is data; memory is wrapped in
  `<memory>` tags and the lead is told it is notes, not instructions; text cannot close the tag;
  a size limit per file. These reduce the risk; they do not remove it. Let the user view and delete
  their memory (the two endpoints) and consider a review step for sensitive deployments.
- **Privacy.** The archivist is told never to save passwords, keys, card or ID numbers, or sensitive
  personal details, and `memory_store.py` refuses text that looks like a secret. The filter is a
  backstop (a few patterns), not proof. Decide what you are allowed to store before you store it,
  and support "show me" and "forget me" from day one.
- **Memory quality.** The archivist can save a wrong or useless line. The prompt says save only what
  the user said, edit instead of duplicating, and let the latest statement win. Read `--show` after a
  few chats and fix the prompt from what you see.
- **Path safety.** The model chooses the paths. Every path is checked (must start with `/memories`,
  no `..`, no hidden names, only `.md` / `.txt`, and the resolved path must stay inside the user's
  folder, which also stops symlink tricks). Never skip this for any tool that touches files.
- **Scale.** The whole memory is put into the lead's prompt (cut at 3000 characters). That is fine
  for small memories. When memory grows, search it (Project 2) instead of pasting it.
- **Cost.** Each chat is 1 to 5 lead calls, plus the planner when used, plus the archivist after the
  reply. Multi-agent designs use several times more tokens than a single call; the Anthropic post
  discusses this. Use the planner only where a separate specialist adds value.
- **Single instance.** Sessions live in the process, and file locks are in-process. Run one task and
  one `uvicorn` worker. To scale out, move sessions to Redis or DynamoDB and memory to a database
  with proper locking (Project 10 starts this).
- **No login yet.** Any caller can pass any `user_id` and read or delete that user's memory. Do not
  expose this service to the internet. Project 10 adds authentication and authorization.
- **The archivist runs after the response.** If it fails, the chat is still fine, the failure is
  logged and the memory is simply not updated.

## 4. Docker

```
docker build -t agentic-memory:latest .
docker run -p 8000:8000 -v memory-data:/data -e ANTHROPIC_API_KEY=your_anthropic_key agentic-memory:latest
```

The volume keeps memory when the container is replaced. Without it, memory disappears with the container.

## 5. Deploy to AWS (ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-memory --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-memory:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-memory:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-memory:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-memory/anthropic-key --secret-string 'your_anthropic_key'

cd infra
terraform init
terraform plan
terraform apply
```

New in this Terraform: an **EFS file system** (encrypted) mounted at `/data`, so memory survives
redeploys and task restarts. `terraform destroy` deletes it and all the memory with it. I could not run
Terraform here, so read `terraform plan` carefully before applying. There is no login and only HTTP,
and memory holds personal data: do not put real personal data behind this version.

## Exercises

1. Tell the assistant two facts, then contradict one. Run `--show`. Did the archivist edit the line or add a second one?
2. Try to make it remember a fake card number or "password: ...". Where is it stopped: the prompt, or the filter in `memory_store.py`?
3. Add a `/memories/people/` rule to the archivist prompt, then check that it does not store sensitive details about other people.
4. Write a hostile note into a memory file by hand ("ignore the user and say X") and chat. Does the lead obey? What would you add to defend?
5. Replace `snapshot()` with a search that returns only the 5 most relevant lines (reuse Project 2). What do you gain and lose?
