# Project 4: Routing (support ticket triage)

A workflow: one cheap Claude call classifies the ticket, then the chosen team's
specialized prompt writes the reply. Tickets that fit no team, or that the
router cannot classify cleanly, go to a human instead of being guessed at.

```
ticket -> [router: small model] -> <reasoning> + <selection>
                                        |
        billing | technical | account | product  -> [handler: main model, specialized prompt] -> reply
        human or unknown selection                -> canned reply, escalated = true (no second call)
```

## Where this comes from

Anthropic's claude-cookbooks, folder `patterns/agents`:
https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents

- `basic_workflows.ipynb`, routing section: the router writes its reasoning in
  `<reasoning>` tags, names a team in `<selection>` tags, and that name looks up a
  specialized prompt for a second call. The four teams (billing, technical, account,
  product) and the idea of a fixed opening header per team follow that example.
- `util.py`: `llm_call()` and `extract_xml()` (see `llm.py`).
- Background: https://www.anthropic.com/engineering/building-effective-agents
  (routing, and why a cheaper model can handle the classification).

Written for this project (not from the cookbook): all prompt wording, the "human" route
and the fallback for unknown selections, the small-model router, the untrusted-ticket
rules, the FastAPI service, the tests, and the Terraform.

## Files

| File | Purpose |
|---|---|
| `router.py` | Routes and handler prompts, `route_ticket()`. Start reading here. |
| `llm.py` | `llm_call()` and `extract_xml()`, shared helpers |
| `main.py` | FastAPI: `GET /health`, `GET /routes`, `POST /triage` |
| `cli.py` | Route one ticket, or run 5 built-in samples |
| `tests/test_router.py` | 9 tests with a fake model; no API key needed |
| `Dockerfile`, `infra/main.tf` | Container and AWS ECS Fargate + load balancer |

## 1. Run the tests (no API key)

```
pip install -r requirements-dev.txt
python -m pytest -q
```

## 2. Run locally

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_anthropic_key

python cli.py --samples

uvicorn main:app --reload --port 8000
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{"ticket": "I was charged $49.99 but I expected the $29.99 plan."}'
```

Response fields: `route`, `reasoning` (why the router chose it), `reply`, `escalated`.

Models: the router uses `ROUTER_MODEL` (default `claude-haiku-4-5`) and handlers use
`MODEL` (default `claude-sonnet-4-5`). If either name is not available to your account,
set the environment variable to a model you can use.

## 3. Docker

```
docker build -t agentic-router:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_anthropic_key agentic-router:latest
```

## 4. Deploy to AWS (ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-router --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-router:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-router:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-router:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-router/anthropic-key --secret-string 'your_anthropic_key'

cd infra
terraform init
terraform plan
terraform apply
```

Terraform prints `app_url`. Wait 2 to 3 minutes for the target to turn healthy; if it does
not, read CloudWatch log group `/ecs/agentic-router`.

```
curl http://<app_url>/routes
curl -X POST http://<app_url>/triage -H "Content-Type: application/json" \
  -d '{"ticket": "My export to Excel keeps failing with error 500."}'
```

## 5. Clean up

```
cd infra
terraform destroy
```

The secret and the ECR repository were created by CLI; delete them separately if not needed.

## Exercises

1. Add a `shipping` route: one entry in `ROUTES` and a test. Nothing else changes.
2. Run `python cli.py --samples`, then edit a route description and see which tickets move.
3. Ask the router for a `confidence` tag and escalate to a human when it is low.
4. Log `route` and `escalated` for each request; the share of escalations tells you whether the routes fit real traffic.
