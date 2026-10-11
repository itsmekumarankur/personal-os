# Project 10 (Capstone): A production-style agent platform

A bank support assistant with everything a real deployment needs around the model:
**login and roles, guardrails, human approval for risky actions, an audit trail, logs and metrics,
alarms, tests that run on every change, an approval-gated deployment pipeline, and infrastructure as code**
for both AWS ECS (Terraform) and Kubernetes/EKS (manifests).

```
 CUSTOMER                                                       REVIEWER (human)
    │  POST /v1/chat  (Bearer key)                                   │
    ▼                                                                │
┌─────────────────────────────────────────────────────────────┐      │
│ 1 request id, timing, JSON log, metrics                      │      │
│ 2 AUTH: key -> who you are + role   (401 / 403)              │      │
│ 3 RATE LIMIT per caller             (429)                    │      │
│ 4 INPUT GUARD: redact card/ID numbers, block known attacks   │      │
│ 5 AGENT LOOP (model + tools), daily token budget, turn limit │      │
│      read tool  ──> run now (checks your own account only)   │      │
│      write tool ──> VALIDATE ──> create APPROVAL ──> PAUSE ──┼──────┤
│ 6 OUTPUT GUARD: no card numbers, no other customers' ids     │      │ GET  /v1/approvals
│ 7 AUDIT record for every important step                      │      │ POST /v1/approvals/{id}/decision
└─────────────────────────────────────────────────────────────┘      │
    ▲                                                                ▼
    │  GET /v1/conversations/{id}  <── model writes the outcome ── approve: RE-VALIDATE, run the action
    │                                                              reject:  tell the model "not approved"
 OPS:  /metrics   /v1/audit   alarms -> email         DATABASE (SQLite): conversations, approvals, audit, usage
```

## What this project is, and is not

It is the **production wrapper**: the controls that decide whether you can trust an agent with real
customers. The agent loop is the one from Project 1. It does not re-use every earlier pattern on purpose
(no RAG, routing or parallel steps), so that the controls stay easy to read. The exercises show where those fit.

| Earlier project | Where it shows up here |
|---|---|
| 1 Tool-using agent | `agent.py` loop, `tools.py` |
| 4 Routing | exercise: route "card" and "loan" questions to different prompts |
| 7 MCP | exercise: move `tools.py` behind an MCP server and keep the ownership checks |
| 8 Evaluator-optimizer | `evals/` (quality checks) and the output guard |
| 9 Memory | conversations are stored and survive restarts; user memory is an exercise |
| Docker, ECS, Terraform, EFS | `Dockerfile`, `infra/` |

## Where this comes from

- **Anthropic, "Building effective agents"** (anthropic.com/engineering/building-effective-agents): keep agents
  simple, put stopping conditions and human checkpoints around them, test in sandboxes with guardrails.
  The pause-for-a-human design and the turn limit follow that advice.
- **OWASP Top 10 for LLM applications**: prompt injection, insecure output handling, sensitive information
  disclosure, excessive agency. The threat table below uses those ideas. I could not open the OWASP page
  in this session, so the names are from my background knowledge; check them against the current list.
- **GitHub Actions with AWS (OIDC)** for deployments without stored AWS keys, and the Terraform AWS provider
  docs for the resources. Action versions in the workflows (`checkout@v4`, `setup-python@v5`,
  `configure-aws-credentials@v4`, `amazon-ecr-login@v2`, `setup-terraform@v3`) are from memory: confirm they are current.
- The Prometheus text format (`prometheus_client`) for `/metrics`; the twelve-factor habit of reading settings
  from the environment and failing at start-up if they are wrong.

Written for this project: everything in this folder. It is a teaching design, not a copy of a vendor reference.

## Files

| File | Purpose |
|---|---|
| `main.py` | The API: auth, rate limit, endpoints, request id, metrics middleware. `create_app()` builds it. |
| `agent.py` | The agent loop, human approval flow, budgets, audit calls. **Start here.** |
| `tools.py` | The tools and their **authorization and validation**. |
| `guardrails.py` | Redaction, injection patterns, output checks. |
| `config.py` | Settings and API keys, checked at start-up. |
| `store.py` | SQLite: conversations, approvals, audit log, token usage. |
| `observability.py` | JSON logs, request ids, Prometheus metrics. |
| `ratelimit.py`, `bank.py`, `llm.py` | Rate limiter, sample bank (made-up data), the one place that calls Claude. |
| `tests/` | 67 tests with a fake model; no API key needed. |
| `evals/` | Behaviour checks against the **real** model (`run_evals.py`, `cases.jsonl`). |
| `Dockerfile` | Non-root container. |
| `infra/` | Terraform: ECR, ALB (+HTTPS option), ECS, EFS, secrets access, alarms. |
| `k8s/` | Kubernetes manifests for EKS (kustomize). |
| `.github/workflows/` | `ci.yml` (tests, lint, image, terraform checks), `deploy.yml` (approval-gated deploy), `evals.yml`. |
| `api_keys.example.json` | Demo keys for local use. Never use them anywhere real. |

## 1. Run the tests (no API key)

```
pip install -r requirements-dev.txt
ruff check .
python -m pytest -q
```

## 2. Run it locally and walk through the approval flow

```
export ANTHROPIC_API_KEY=your_anthropic_key
export API_KEYS_JSON="$(cat api_keys.example.json)"
uvicorn main:create_app --factory --port 8000
```

In another terminal:

```
CUST=demo-customer-1-key-change-me-0001
APPR=demo-approver-key-change-me-000003
OPS=demo-ops-key-change-me-00000000004
H='Content-Type: application/json'

# 1. a read-only question
curl -s -X POST localhost:8000/v1/chat -H "$H" -H "Authorization: Bearer $CUST" -d '{"message":"What is my balance?"}'

# 2. a risky request: the answer says it is waiting for a human; note conversation_id and approval_id
curl -s -X POST localhost:8000/v1/chat -H "$H" -H "Authorization: Bearer $CUST" -d '{"message":"My card C-9001 is lost, please freeze it"}'

# 3. the reviewer sees it, with the customer's words
curl -s localhost:8000/v1/approvals -H "Authorization: Bearer $APPR"

# 4. the reviewer decides (approve or reject); the action runs only now
curl -s -X POST localhost:8000/v1/approvals/<approval_id>/decision -H "$H" -H "Authorization: Bearer $APPR" \
  -d '{"decision":"approve","note":"verified by phone"}'

# 5. the customer reads the outcome
curl -s localhost:8000/v1/conversations/<conversation_id> -H "Authorization: Bearer $CUST"

# 6. operations
curl -s localhost:8000/v1/audit -H "Authorization: Bearer $OPS"
curl -s localhost:8000/metrics -H "Authorization: Bearer $OPS"
```

Also try: ask for account `A-1002` (a different customer), paste a test card number `4111 1111 1111 1111`,
send "ignore all previous instructions", or use the customer key on `/v1/approvals`. Watch the audit log and metrics each time.
The sample bank is in memory, so a restart resets cards and balances but not conversations or approvals.

Settings (environment variables): `API_KEYS_JSON` (required), `ANTHROPIC_API_KEY`, `MODEL`, `DB_PATH`,
`RATE_LIMIT_PER_MIN` (30), `DAILY_TOKEN_BUDGET` (200000 per customer per day), `MAX_REFUND` (5000), `MAX_TURNS` (6),
`INPUT_GUARD` (`block` or `log`), `LOG_LEVEL`, `ENABLE_DOCS` (`1` shows /docs; off by default).
A wrong setting stops the service at start-up with a clear message.

## 3. Evals: does the real model behave?

```
python evals/run_evals.py
```

Seven cases, end to end through the HTTP API: a freeze request must wait for a human; a customer sees only their own
balance; another customer's data is not shared; the EMI is right; an injection attempt is blocked; a refund above the
limit is never requested; someone else's card cannot be frozen. Costs a few cents. Run it before releases and whenever you
change the prompt, the tools or the model. `evals.yml` runs it by hand or nightly. A failure may be real or may be
model variation: run again, then change the prompt, the tool descriptions or the case.

## 4. Threat model: what is protected, how, and where to see it

| Risk | Control | Code | Test |
|---|---|---|---|
| Anyone calls the API | API keys with roles; 401 / 403; constant-time key comparison | `config.py`, `main.py` | `test_missing_or_wrong_key_is_401`, `test_roles_are_separated` |
| A customer reads another customer's data | The model **never supplies an account id**; ids it does supply (card, transaction) must belong to the caller; conversations return 404 for non-owners | `tools.py`, `main.py` | `test_a_customer_cannot_reach_another_customers_data`, `test_cannot_request_actions_on_other_peoples_things`, `test_conversations_belong_to_their_owner` |
| The model is tricked into a harmful action | Write tools **cannot run without a human**; arguments validated in code; one action per turn; refund limits checked before a human is bothered | `agent.py`, `tools.py` | `test_write_tool_waits_for_a_human_and_does_not_run`, `test_refund_rules_are_checked_before_a_human_is_bothered` |
| Approval races or stale approvals | Atomic pending-to-decided update (one winner); action **re-validated at execution**; failures recorded | `store.py`, `agent.decide` | `test_a_decision_can_only_be_made_once`, `test_action_is_revalidated_when_it_finally_runs` |
| Card numbers and IDs leak into the model, database or logs | Luhn-checked redaction before anything else; logs carry sizes, ids and outcomes, never message text | `guardrails.py`, `observability.py` | `test_card_numbers_never_reach_the_model_or_the_database`, `test_json_log_lines_have_a_request_id_and_no_message_text` |
| Prompt injection | Pattern block, system prompt that treats text as data, **and** the controls above (the real defence) | `guardrails.py`, `agent.py` | `test_prompt_injection_is_blocked_without_calling_the_model` |
| Unsafe model output | Output guard removes card numbers and other customers' account ids | `guardrails.check_output` | `test_output_guard_removes_cards_and_other_accounts` |
| Cost and abuse | Per-caller rate limit, daily token budget, turn limit, input size limit, model timeout | `ratelimit.py`, `agent.py`, `llm.py` | `test_rate_limit_per_caller`, `test_daily_token_budget`, `test_turn_limit_stops_endless_tool_loops` |
| Model outage | Clean 502; a decided approval still gets a fixed outcome message if the model is down | `agent.py` | `test_model_failure_is_a_clean_502`, `test_if_the_model_is_down_when_a_decision_comes_in_...` |
| Internals leak in errors | Generic 500 with a request id; `/docs` off by default | `main.py` | `test_unexpected_errors_do_not_leak_details`, `test_docs_endpoints_are_off_by_default` |
| Bad releases | CI gates; immutable image tags; reviewer approval before deploy; automatic rollback; smoke test | `.github/workflows`, `infra/main.tf` | (pipeline, not unit-tested) |
| Compromised container | Non-root user; container can read only two secrets; only the load balancer can reach it; dropped capabilities on Kubernetes | `Dockerfile`, `infra/`, `k8s/` | (infrastructure) |

The most important design rule: **authorization lives in code, not in the prompt.** The prompt asks the model to behave;
`tools.py` makes sure that even a model that misbehaves cannot do harm.

## 5. Observability

**Logs.** One JSON object per line, with `request_id`, `event`, `status`, `ms`, `principal` and, for guardrail events,
`kind`. Customer message text is never logged. Useful CloudWatch Logs Insights queries:

```
fields @timestamp, path, status, ms, principal, request_id
| filter event = "http_request" and status >= 500
| sort @timestamp desc | limit 50

fields kind | filter event = "guardrail" | stats count() by kind

fields @timestamp, event, @message | filter request_id = "PUT-A-REQUEST-ID-HERE" | sort @timestamp
```

The load balancer health check calls `/health` often; filter `path != "/health"` when reading logs.
Every response carries `X-Request-ID`; give it to support and you can find every line for that request.

**Metrics** (`/metrics`, ops key): request counts and latency by route template, tool calls by outcome, guardrail events by
kind, approvals by event, model tokens in and out, model errors, and the number of approvals waiting. Labels never contain
raw URLs or model-chosen tool names, so a caller cannot create unlimited time series.

**Alarms** (Terraform): server errors, unhealthy target, high CPU, spike in guardrail events, spike in failed logins. They
send email through SNS when `alarm_email` is set.

**Audit** (`/v1/audit`, ops key): who did what and when: chats, tool calls, rejected tool calls, approvals requested,
decisions, executed actions, guardrail events. It stores ids and outcomes, not message text.

**Not included:** distributed tracing (OpenTelemetry), dashboards, and a metrics store. `/metrics` is ready for Prometheus
to scrape; on ECS you would add the CloudWatch agent or a sidecar.

## 6. CI/CD

```
 pull request ──> ci.yml: ruff, tests, build image and start it, terraform fmt/validate
 tag v1.2.0   ──> deploy.yml:
                     ci.yml again ──> WAIT for a human (GitHub environment "production")
                     ──> OIDC login to AWS ──> terraform init (remote state)
                     ──> create ECR repo ──> build and push image tagged with the commit id
                     ──> terraform plan ──> apply ──> ECS replaces the task
                     ──> circuit breaker rolls back if it never becomes healthy
                     ──> smoke test on /health
 nightly      ──> evals.yml: real-model behaviour checks
```

**One-time setup**

1. Create the two secrets (values stay out of Terraform and Git):
   ```
   aws secretsmanager create-secret --region ap-south-1 --name agentic-platform/anthropic-key --secret-string 'your_anthropic_key'
   aws secretsmanager create-secret --region ap-south-1 --name agentic-platform/api-keys --secret-string file://api_keys.json
   ```
   Make `api_keys.json` from `api_keys.example.json` with **long random keys**:
   `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`. The secret value is the raw JSON text.
2. Create an S3 bucket (private, versioned) and a DynamoDB table with key `LockID` for Terraform state.
3. In AWS IAM create an OIDC identity provider for `token.actions.githubusercontent.com` and a role that GitHub can assume,
   limited to your repository and the `production` environment:
   ```json
   { "Effect": "Allow", "Principal": { "Federated": "arn:aws:iam::<account_id>:oidc-provider/token.actions.githubusercontent.com" },
     "Action": "sts:AssumeRoleWithWebIdentity",
     "Condition": { "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                                      "token.actions.githubusercontent.com:sub": "repo:<owner>/<repo>:environment:production" } } }
   ```
   Give the role the permissions Terraform needs (ECR, ECS, EC2 networking, ELB, EFS, IAM roles, CloudWatch, SNS,
   Secrets Manager read, and the state bucket and table). Start in a sandbox account; tighten from what `terraform plan`
   uses. Do not give it administrator access in production.
4. In GitHub: Settings, Environments, create `production` and add **required reviewers**. Add repository variables
   `AWS_DEPLOY_ROLE_ARN`, `TF_STATE_BUCKET`, `TF_LOCK_TABLE`, and the secret `ANTHROPIC_API_KEY` (for evals).

**Release:** `git tag v1.0.0 && git push --tags`, approve the waiting deployment in GitHub.
**Roll back:** Actions, Deploy, Run workflow, set `ref` to the previous tag. (ECS also rolls back by itself when a new
version never becomes healthy.)

**Deploying by hand without GitHub** (for learning):

```
cd infra
terraform init
terraform apply -target=aws_ecr_repository.this -var image_tag=first
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com
docker build -t <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-platform:first ..
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-platform:first
terraform apply -var image_tag=first -var alarm_email=you@example.com
```

HTTPS: create an ACM certificate for your domain in `ap-south-1`, then add `-var certificate_arn=...`. Without it the
stack serves plain HTTP, where API keys travel unencrypted: use it only for learning.

## 7. Kubernetes (EKS) path

Assumes a cluster with the AWS Load Balancer Controller, the EBS CSI driver with a `gp3` storage class, and a way to
create the secret (see `k8s/secret.example.yaml`).

```
docker build -t <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-platform:v1 .
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-platform:v1

kubectl create secret generic agent-platform-secrets \
  --from-literal=ANTHROPIC_API_KEY='your_anthropic_key' --from-file=API_KEYS_JSON=./api_keys.json

cd k8s
kustomize edit set image ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/agentic-platform=<account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-platform:v1
# edit ingress.yaml: certificate-arn
kubectl apply -k .
kubectl rollout status deployment/agent-platform
```

The manifests run as a non-root user with a read-only filesystem, dropped capabilities, resource limits, and separate
liveness (`/health`) and readiness (`/ready`) probes. Strategy is `Recreate` with one replica because of SQLite. There is
deliberately **no autoscaler**: it would start more writers.

## 8. Runbook (first moves when an alarm fires)

| Alarm | Look at | Usual cause and action |
|---|---|---|
| 5xx errors | Logs Insights 5xx query, then the `request_id` | Model outage (`llm_error` events): wait or check the API status. Bug after a release: roll back. |
| Unhealthy target | ECS service events, log group | Bad settings (the app stops with `ConfigError`), missing secret, EFS mount failing. Fix, or roll back. |
| High CPU | `/metrics`, request rate | Traffic spike or loop. Check the rate limit and `DAILY_TOKEN_BUDGET`. |
| Guardrail spike | `stats count() by kind` | `prompt_injection` or `auth_failed`: someone probing. Block the key or IP. `output_foreign_account`: investigate the prompt, this means the model tried to mention someone else's id. |
| Approvals piling up | `agent_pending_approvals`, `/v1/approvals` | Reviewers are not looking. There is no alarm for this yet (exercise). |

## 9. Honest production-readiness list

**Done and tested in this folder:** authentication and roles, per-caller rate limit, token budget, input and output
guardrails, human approval with re-validation, audit trail, JSON logs without message text, metrics, restart-safe state,
configuration checks at start-up, seven real-model eval cases (written, not run by me).

**Partly done:**
- *Single instance only.* SQLite has one writer, and the rate limiter and Bank are in memory. Before scaling out, replace
  `store.py` with Postgres or DynamoDB, move rate limiting to the gateway or Redis, and use a real back end for the bank.
  SQLite on a network file system (EFS) is also not recommended for heavy use.
- *Keys.* API keys live in one JSON secret, are compared as plain strings, and have no rotation tooling. Production usually
  uses single sign-on for staff and an API gateway for customers.
- *Injection guard.* Patterns catch the obvious, not the clever. The real protection is authorization in code and human approval.
- *Audit log.* It sits in the same database as everything else, so it is not tamper-proof. Ship it to write-once storage.
- *HTTPS* needs a certificate and a domain you provide.

**Not done:** tracing, dashboards, WAF, backups (turn on AWS Backup for EFS/EBS), data retention and deletion rules, multi-AZ
high availability, load testing, a security review by someone other than the author, and a compliance review of what customer
data may go to a model provider.

**Not verified by me:** I ran the unit and API tests (67 pass) and started the server locally with the real web server. I did
**not** run the live Claude API, Docker, GitHub Actions, AWS or Kubernetes. Terraform was checked for syntax and formatting only
(`terraform validate` needs the AWS provider, which I could not download here), and the YAML files were checked to parse. Expect
to fix small things on your first real run, and read `terraform plan` before every apply.

## Exercises

1. Add a write tool `block_upi_id(upi_id)` that needs approval. Which three places must change? (Hint: `tools.py`, the eval cases, the tests.)
2. Four-eyes rule: refunds above 2000 need **two** different approvers. Where does the second decision live?
3. When an approval is requested, notify reviewers (email or Slack) without blocking the request. Why is an outbox table safer than calling Slack inside `_run_loop`?
4. Add an alarm for "an approval has been waiting more than 30 minutes".
5. Replace `store.py` with Postgres. Which methods change? Does the rest of the code notice?
6. Add OpenTelemetry tracing so one request shows the model calls and tool calls as spans.
7. Write an eval case that currently fails (for example a customer asking to change their address). Fix it with the prompt, then with a tool. Which fix is more reliable?
8. Move `tools.py` behind an MCP server (Project 7). Where does the caller's identity come from now, and how does the server know it?
