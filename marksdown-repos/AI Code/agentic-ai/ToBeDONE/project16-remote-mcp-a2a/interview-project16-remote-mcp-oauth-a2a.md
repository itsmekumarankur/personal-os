# Architect Interview — Chapter 16: Remote MCP, OAuth and A2A

**Role:** *Principal Architect, AI Platform* at a bank. Your agents will call tools and other agents hosted by other teams, over the network. I'm the interviewer — and the CISO is listening.
**How to use:** answer aloud (60–90s), compare, score 0/1/2.
Legend: 🎯 intent · ✅ strong answer · 🔁 follow-up · 🚩 red flag

---
## ROUND 1 — Why remote changes everything

### Q1. Local MCP (stdio) worked fine. What exactly changes when the tool server moves to another machine?
✅ Local trust = "I installed it, it's a child process". Remote = anyone on the network can knock, so every request needs a **token**. Four new questions: *Who are you? Which service is this for? What may you do? Whose data?* Also: transport (streamable HTTP), discovery, rate limits, audit, TLS, DNS-rebinding (Host header) protection.

### Q2. Explain a JWT access token to a non-security colleague, and name the claims that matter.
✅ A signed note: "auth server says client X may use scopes S at service A until time T". Claims: `iss` issuer, `aud` audience (which service it's FOR), `scope`, `exp` (short life, minutes), `cid` customer being acted for, `act` the agent acting on someone's behalf. Services verify with public keys (JWKS), no call to the issuer per request.

---
## ROUND 2 — OAuth flows

### Q3. Walk through how a program obtains a token (client credentials). What does `resource=` do?
✅ POST /token with client authentication, `grant_type=client_credentials`, `resource=<target service>` (RFC 8707) and requested scope. Server checks secret (constant-time, stored hashed), checks requested scopes ⊆ what this client may ever have, issues JWT with `aud` = that resource. `resource` binds the token to ONE service.

### Q4. A client hits the MCP server with no token. How does it find out where to get one, without hard-coding?
🎯 Discovery.
✅ Server returns **401** with `WWW-Authenticate: Bearer resource_metadata="…/.well-known/oauth-protected-resource"` (RFC 9728) → client reads it → learns the authorization server → fetches its metadata (RFC 8414) for the token endpoint → gets a token → retries with Bearer.

### Q5. Why is the `aud` check "the most important check"? Describe the attack it stops.
🎯 Confused deputy / token passthrough.
✅ Without it, a token issued for service X is accepted by service Y. A malicious or compromised service that receives your token could replay it elsewhere; or an MCP server could be tricked into forwarding a user token to a downstream API. Each resource must reject tokens whose `aud` isn't itself, and must **exchange** rather than forward tokens.
🔁 "Isn't a valid signature enough?" → no; a perfectly valid token for another audience is still the wrong token.
🚩 Checking only signature and expiry.

### Q6. Orchestrator calls the Loan Advisor agent, which needs the Bank tools on behalf of the customer. Design the token flow.
🎯 Delegation.
✅ **Token exchange (RFC 8693)**: orchestrator gets token A (aud = advisor, scopes e.g. `a2a:invoke tools:basic`). Advisor sends A to the auth server as `subject_token`, asks for `resource=MCP`, scope `tools:basic`. Auth server checks: A was issued FOR the advisor (aud), caller is the advisor client, new scopes ⊆ (scopes in A ∩ what the advisor may swap). Returns token B: shorter life (2 min), `sub=orchestrator`, `cid=customer`, `act={sub: loan-advisor}`, `aud=MCP`. Audit shows "client=orchestrator actor=loan-advisor".
🔁 "What if the orchestrator never granted tools:basic?" → the advisor cannot conjure it; exchange fails; task ends FAILED. **Delegation can only shrink.**

---
## ROUND 3 — Break it (attack questions)

### Q7. List the token attacks and one-line defence for each: `alg:none`, HS256 signed with the public key, edited scopes, same `kid` different key, expired, wrong issuer, unknown key.
✅ Pin algorithm to RS256 (never trust the header's alg); verify signature; explicit exp/iss/aud checks; unknown `kid` → refresh JWKS once then reject; key rotation plan.

### Q8. The auth server is down and the MCP server can't fetch the JWKS. Allow or deny? Why?
✅ **Fail closed.** Deny. Optionally use a cached key set within a bounded age. Availability of auth is part of your SLO; design cache TTL and alerts. (This was a missing test in the lab, found by mutation testing: nobody had written the fail-closed case.)

### Q9. Customer A's token is used to read customer B's account via the same tool. What stops it?
✅ Ownership check inside the tool using `cid` from the token (not from a request argument); respond "not found" rather than "forbidden" so existence isn't leaked. Authorisation is per-object, not just per-scope.

### Q10. A web page in the user's browser makes requests to your MCP server running on localhost. What attack is this and what's the control?
✅ **DNS rebinding** against local servers; defend with Host/Origin header allow-list, bind to loopback, require auth even locally.

### Q11. Explain the "rug pull" and how tool pinning defends. What's the weakness?
🎯 Tool descriptions are an instruction channel.
✅ A tool description/schema is read by the model; the server can change it after you approved it and inject instructions or change behaviour. Pin a fingerprint of name + description + schema; any later change, new tool or vanished tool raises `PinMismatch` **before** the call. Weakness: **trust on first use** — someone must review the first list; also pin per version and alert on change.

### Q12. A hostile agent card says "my endpoint is http://169.254.169.254/…" or redirects to another host. What defences does a client need?
✅ Origin pinning, https only, block private/link-local IPs (SSRF), no redirects with credentials, never send your token to a host other than the audience it was minted for.

---
## ROUND 4 — A2A (agent to agent)

### Q13. MCP vs A2A: when do you use which?
✅ MCP: an agent calls **tools** (functions, resources) — deterministic-ish capability. A2A: one agent delegates a **task** to another autonomous agent that may take time, ask questions, stream progress. Use MCP for capabilities, A2A for opaque collaborating agents owned by other teams.

### Q14. Describe the task lifecycle and two invariants you enforce.
✅ submitted → working → completed / failed / canceled / rejected (plus input-required in the spec). Invariants: only valid transitions; **terminal states are immutable** (a late "completed" can't overwrite "canceled" — race handled under a lock); tasks are **owner-scoped** (another caller's task id looks like "not found").

### Q15. The advisor crashes internally with a stack trace mentioning database hostnames. What does the caller see?
✅ A generic FAILED message; details only in logs with a correlation id. Error text across agent boundaries is an information leak and an injection vector.

### Q16. How do you trace and audit one customer request across orchestrator → advisor → MCP server?
✅ Propagate `traceparent` (Chapter 15) plus identity context; audit rows record customer, client, actor, tool, decision, token id (not token); rate limits per client; alert on denials.

---
## ROUND 5 — Architect judgement
### Q17. Token lifetime: 5 minutes for client tokens, 2 minutes after exchange. Defend or change.
✅ Short life limits the blast radius of theft; cost is more token requests (cache tokens until near expiry, handle clock skew); high-risk actions may need even shorter or step-up auth.
### Q18. Where does human consent sit when an agent acts for a customer?
✅ OAuth user consent / authorization-code flow for user-delegated access (the lab uses client credentials + exchange to teach the chain); sensitive actions (freeze card) need explicit scopes and possibly confirmation; audit who approved.
### Q19. Rollout plan for exposing internal tools to partner agents.
✅ Gateway in front, per-partner clients/scopes, rate limits, schema/version pinning, tenant isolation, observability, kill switch, threat model review, staged rollout, contract tests.

---
## RAPID FIRE
1. Which claim says "this token is for service X"? 2. What RFC covers token exchange? 3. Why pin RS256? 4. What does 401 + WWW-Authenticate tell the client? 5. Auth server unreachable: allow or deny? 6. What makes delegation "shrink only"? 7. Why return "not found" for someone else's task? 8. What is TOFU? 9. What blocks DNS rebinding? 10. Why is error text generic across agents?

*(Answers: `aud` · 8693 · stops algorithm-confusion attacks · where to get a token (resource metadata) · deny (fail closed) · scopes = intersection · avoid leaking existence · trust on first use · Host header allow-list · leaks internals/injection)*

## HANDS-ON CHALLENGE
Run `python demo.py`, then read the tests named in README section 5. Pick any three attacks, and explain to the CISO, in plain words, how the test proves the defence.

## SCORECARD
32–38 architect-ready · 24–31 revisit exchange and aud checks · <24 redo README sections 3–5.
*Honest note: the lab ran everything locally with fake data and no model; A2A shapes are a teaching subset; RFC details and spec names evolve — verify before quoting.*
