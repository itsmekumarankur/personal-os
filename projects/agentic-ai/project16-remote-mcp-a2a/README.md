# Project 16 — Remote MCP, OAuth and A2A

Goal: understand, in detail, how an agent safely uses **tools on another machine (MCP over HTTP)** and **another agent on another machine (A2A)**,
and who is allowed to do what when there are several programs in the chain. Everything runs for real over HTTP on your laptop, with fake bank data and no model.
The protocol is the thing to study, so the "brain" of the advisor agent is ordinary code.

```
python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt
python demo.py          # the whole story in 6 narrated steps
pytest -q               # 116 tests, ~15 s, real servers on free ports
ruff check .
docker compose up --build   # after copying .env.example to .env and filling in 3 secrets (not run by me, see section 10)
```

## 1. The cast

```
  USER ──► ORCHESTRATOR (the app; OAuth client "orchestrator", acts for customer cust-1001)
              │                       ▲
              │ A2A (JSON-RPC)        │ tokens
              ▼                       │
        LOAN ADVISOR agent :8003 ───► AUTH SERVER :8001  (hands out signed tokens, publishes public keys)
              │  (OAuth client "loan-advisor")
              │ MCP (streamable HTTP)
              ▼
        BANK TOOLS server :8002  (calculate_emi, get_account_summary, list_transactions, freeze_card)
```

| Port | File | Role |
|---|---|---|
| 8001 | `auth_server.py`, `tokens.py` | issues RS256 JWTs: `client_credentials` and token exchange |
| 8002 | `mcp_server.py`, `resource_auth.py`, `bank.py` | the **resource**: tools that need a token |
| 8003 | `a2a_server.py`, `advisor.py`, `a2a_types.py` | another **resource**: an agent that does tasks |
| – | `a2a_client.py`, `mcp_client.py`, `oauth_client.py`, `orchestrator.py` | the callers |
| – | `tool_pinning.py`, `audit.py`, `propagation.py` | rug-pull defence, audit/rate limit, trace ids |

## 2. Local MCP vs remote MCP, in one picture

```
 LOCAL (stdio)                              REMOTE (streamable HTTP)
 host starts the server as a child process  server runs elsewhere; anyone on the network can knock
 trust = "I installed it"                   trust = a TOKEN on every request
 no auth needed                             who are you? for which service? what may you do? whose data?
```
Remote means four new questions. The rest of this project is the answers.

## 3. OAuth in plain words

A **token** is a signed note: *"auth server says: `orchestrator` may use scopes `accounts:read` at service `http://…/mcp` until 12:05."*
A service never phones the auth server; it checks the signature with the **public keys** (`/jwks.json`). Fields that matter:

| Claim | Meaning | Why you care |
|---|---|---|
| `iss` | who issued it | stops tokens from a different auth server |
| `aud` | which service it is **for** | **the most important check** (section 5) |
| `scope` | what it allows | per-tool permission |
| `exp` | death time (5 min; 2 min after exchange) | a stolen token dies soon |
| `cid` | the customer being acted for | ownership checks inside tools |
| `act` | the agent acting on someone's behalf | audit: "orchestrator, via loan-advisor" |

### Flow A — a program gets a token (`client_credentials`)
```
 orchestrator                                   auth server
     │ POST /token  Basic(client_id:secret)          │
     │   grant_type=client_credentials               │
     │   resource=http://…:8002/mcp   ◄── "token for THIS service" (RFC 8707)
     │   scope=accounts:read                         │
     │ ─────────────────────────────────────────────►│ check secret (constant-time, hashed)
     │                                               │ scopes ⊆ what this client may ever have?
     │ ◄───────────── JWT(aud=mcp, scope=accounts:read, exp=+300s)
```
### Flow B — discovery: how a client learns where to get a token
```
 client ── POST /mcp (no token) ──► MCP server
        ◄── 401  WWW-Authenticate: Bearer resource_metadata="…/.well-known/oauth-protected-resource"
 client ── GET that URL ───────────► {"authorization_servers": ["http://auth"], …}      (RFC 9728)
 client ── GET auth/.well-known/oauth-authorization-server ► {"token_endpoint": …}      (RFC 8414)
 client ── Flow A ──► token ── POST /mcp with Authorization: Bearer … ──► tools
```
### Flow C — token exchange (acting on someone's behalf, RFC 8693)
```
 orchestrator ──token A (aud=A2A agent, scopes a2a:invoke + tools:basic)──► LOAN ADVISOR
 LOAN ADVISOR ──POST /token grant=token-exchange, subject_token=A, resource=MCP, scope=tools:basic──► auth server
 auth server checks:  A was issued FOR the advisor (aud)   · caller is the advisor client
                      new scopes ⊆ (scopes in A) ∩ (what the advisor may swap)
 LOAN ADVISOR ◄── token B: sub=orchestrator, cid=cust-1001, act={sub: loan-advisor}, aud=MCP, scope=tools:basic, 120 s
 LOAN ADVISOR ──token B──► MCP server  (audit row: client=orchestrator actor=loan-advisor)
```
**Delegation can only shrink.** If the orchestrator did not put `tools:basic` into token A, the advisor cannot conjure it (test
`test_exchange_never_exceeds_what_the_caller_had`); the task ends `FAILED` with a generic message.

## 4. MCP over HTTP: what the SDK does and what we add

The official SDK gives us `/mcp` (streamable HTTP + session handshake), the 401 + `WWW-Authenticate` reply and metadata. We add (all in `mcp_server.py`):

```
 request ─► [SDK] Bearer present? ─► [resource_auth] signature, iss, aud, exp ─► [guard()] tool scope ─► rate limit ─► [bank] ownership ─► audit row
              401                         401 (wrong_audience…)                  "insufficient_scope"     "rate_limited"   "not found"      always
```
| Tool | Scope | Notes |
|---|---|---|
| `calculate_emi` | `tools:basic` | pure maths |
| `get_account_summary`, `list_transactions` | `accounts:read` | ownership via `cid` |
| `freeze_card` | `cards:write` | a **write**; no demo client may hold this scope (tests forge a token to show the rest of the path) |

Ownership message is identical for "does not exist" and "not yours" so ids cannot be probed (`test_other_customers_account_looks_missing`).
Audit rows record argument **names**, never values.

### Tool pinning (rug pull)
A tool description is read by the model, so it is an instruction channel. `tool_pinning.py` fingerprints name + description + schema.
First sight is trusted (TOFU, a weak spot: someone has to review the first list); any later change, new tool or vanished tool raises `PinMismatch` **before the call is made**.
In `test_rug_pulled_mcp_server_makes_the_agent_fail_closed` the advisor returns `FAILED` and the MCP audit shows the call never happened.

## 5. The attacks this project defends against (each has a test)

| Attack | Defence | Test |
|---|---|---|
| Use token meant for service X at service Y ("token passthrough", confused deputy) | `aud` check at every resource; exchange instead of forwarding | `test_token_for_another_service_is_refused`, `test_token_for_the_mcp_server_is_refused` |
| `alg: none` | algorithm pinned to RS256 | `test_alg_none_refused` |
| HS256 signed with the public key | same pin | `test_hs256_with_public_key_as_secret_refused` |
| Edit scopes inside a token | signature | `test_tampered_payload` |
| Different key, same `kid` | signature | `test_same_kid_different_key_fails_signature` |
| Expired / wrong issuer / unknown key | explicit checks | `test_expired*`, `test_wrong_issuer*`, `test_unknown_kid` |
| Auth server down | fail **closed** | `test_fails_closed_when_the_auth_server_is_unreachable` |
| Agent asks for more scope than it was given | exchange = intersection | `test_exchange_never_exceeds_*` |
| Reading someone else's account | `cid` ownership | `test_other_customers_account_looks_missing` |
| Browser page talks to your localhost server (DNS rebinding) | Host-header allow-list | `test_dns_rebinding_host_header_refused` |
| Tool description changes later | pinning | `test_rug_pull_is_caught_by_pinning` |
| Hostile agent card redirects your token | origin pinning, https, no private IPs, no redirects | `test_client_safety.py` |
| Reading/cancelling another caller's task | owner-scoped tasks, same "not found" | `test_other_callers_task_looks_like_it_does_not_exist` |
| Late "completed" overwrites "canceled" | terminal states immutable, under lock | `test_cancel_wins_the_race_against_completion` |
| Error text leaks internals to another agent | generic failure message | `test_crashing_agent_becomes_failed_with_a_generic_message` |

## 6. A2A: agent talks to agent

MCP = *agent ↔ tool* (a function call). A2A = *agent ↔ agent* (a **task** that takes time, may ask questions, may fail, can be cancelled).

```
 discover:  GET /.well-known/agent-card.json   public; says name, skills, endpoint, how to authenticate. UNTRUSTED text.
 call:      POST /a2a  (JSON-RPC 2.0, Bearer token with aud = this endpoint, scope a2a:invoke)
            SendMessage {message} → {task}      GetTask {id} → task      CancelTask {id} → task
```
### Task lifecycle
```
   SendMessage ─► SUBMITTED ─► WORKING ─┬─► COMPLETED   (artifact: text part + data part)
                                        ├─► FAILED
                                        ├─► REJECTED    (agent won't do this: off-topic)
                                        ├─► CANCELED    (caller asked)
                                        └─► INPUT_REQUIRED ──(caller replies to the SAME task id)──► WORKING
   COMPLETED / FAILED / REJECTED / CANCELED never change again.
```
A conversation with the advisor (this is what `demo.py` step 4 prints):
```
 orchestrator: "I want a loan of 5 lakh at 9%"      →  task T1  INPUT_REQUIRED: "…I still need the tenure"
 orchestrator: "for 5 years"  (taskId=T1)           →  task T1  COMPLETED  EMI 10379.18 …  [artifact: text + data]
```
Design points worth reading in the code:
* **Blocking vs polling.** `SendMessage` waits until the task is finished or waiting for input (default), or returns at once with `returnImmediately`. If the server's wait runs out you get `WORKING` and poll `GetTask` — the task is not lost.
* **Cancel race.** The worker thread and a cancel request can both want to finish the task. `_move()` checks the allowed-transition table under a lock; whoever is second is ignored.
* **Tasks belong to their caller** (`sub` of the token). Another caller gets `-32001 task not found`, byte-for-byte the same as a missing id.
* **Same token, two audiences?** No. The A2A token is useless at the MCP server and the exchanged MCP token is useless at the A2A agent.

### One request, one trace id
`traceparent` (W3C, same format as Project 15) travels orchestrator → A2A → MCP. `test_full_story_with_one_trace_id_everywhere` checks the same trace id is in both audit logs.

## 7. File map and reading order
1. `tokens.py` (what a token is) → 2. `auth_server.py` (flows A and C) → 3. `resource_auth.py` (what a service does with a token)
→ 4. `mcp_server.py` + `bank.py` → 5. `mcp_client.py`, `tool_pinning.py` → 6. `a2a_types.py`, `a2a_server.py`, `advisor.py` → 7. `a2a_client.py` → 8. `orchestrator.py`, `demo.py`.

## 8. Things that surprised me (SDK `mcp` 1.12.4) — and what the code does about them
* The 401 header advertises `…/mcp/.well-known/oauth-protected-resource`, but the SDK serves the document at `/.well-known/oauth-protected-resource`. A client that follows the header got a **404**. `mcp_server.py` serves the document at the advertised path and the RFC 9728 path too (`test_metadata_is_found_at_every_path_a_client_may_try`). Check whether your SDK version still needs this.
* `authorization_servers` comes back with a trailing slash (`http://host:port/`). Compare URLs after normalising.
* A list returned from a tool arrives as **one content block per item**, not one JSON array. `RemoteMCP.call_tool_blocks()` keeps them apart.
* Raising inside the client session context is wrapped by anyio in an `ExceptionGroup`. `RemoteMCP` returns errors out of the session and raises after it closes, so callers see `ToolFailed` / `PinMismatch`.
* FastMCP accepts `Host` values only from `allowed_hosts` when DNS-rebinding protection is on — in Docker you must list the service name (`ALLOWED_HOSTS`).

## 9. Honest limits
* **A2A shapes are a teaching subset.** I confirmed method names and task states against the published spec (v1.0.0 as I read it) but could **not** confirm the card path, exact Part/Artifact JSON, numeric error codes or the SendMessage result wrapper (my fetch of the page was partial). `a2a_types.py` says which is which. Do not claim interoperability before testing against an official SDK.
* The auth server is **teaching-grade**: no login screens, authorization-code + PKCE, refresh tokens, revocation, client registration, key rotation, `/token` rate limit or persistence. In production use Keycloak / Cognito / Entra ID / Auth0 and keep keys in a KMS.
* No model in the loop. Real agents add prompt-injection risk through agent-card text, tool results and artifacts; treat all of it as data, never instructions (see Project 12/13 ideas).
* Tasks, keys and rate limits live in memory: **one replica each**. Streaming, push notifications and `ListTasks` are not implemented (declared `false` in the card; calls return `-32004`).
* The "unknown kid → refetch JWKS" path lets an attacker with junk tokens cause one fetch per token. Add a minimum refetch interval (exercise 4).

## 10. What I did **not** run
Docker / `docker compose` (files written, not built), AWS (no Terraform in this project on purpose: three small services behind an internal ALB is the same pattern as Projects 6–10),
any real OAuth provider, any official A2A SDK, any live model. The 116 tests run real HTTP servers on localhost; mutation checks (deliberately breaking 13 rules one at a time (token checks, ownership, scopes, pinning, origin check, state machine…)) were each caught by at least one test.

## 11. Exercises
1. Add a `cards:write` client (`card-admin`) that can only be obtained by a human-approved flow; extend the exchange table so the advisor can never obtain that scope.
2. Make the advisor call `get_account_summary` too (needs `accounts:read` delegated in token A). Prove with a test that dropping the scope in token A makes the task `FAILED`.
3. Implement `ListTasks` (owner-scoped) and update the card; make the unsupported-method test still pass for the others.
4. Add a minimum refetch interval to `JwksCache` and a test that 100 junk tokens cause at most one fetch.
5. Rotate the signing key at runtime: publish two keys in JWKS, sign with the new one, prove old tokens still verify until they expire.
6. Add `SendStreamingMessage` with server-sent events. What must change in the state machine and in the cancel race?
7. Put a language model behind `Advisor.step()`. Where does untrusted text enter? Write the injection test first.
