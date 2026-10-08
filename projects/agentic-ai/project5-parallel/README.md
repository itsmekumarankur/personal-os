# Project 5: Parallelization (design review panel + voting)

Two ways to run model calls at the same time, built on one small helper.

```
SECTIONING   design -> [security] [reliability] [performance] [cost] [maintainability]   (all at once)
                              \         \            |            /          /
                               Python: worst verdict wins  +  1 call writes the summary

VOTING       text + yes/no question -> [vote 1] [vote 2] [vote 3] [vote 4] [vote 5]      (all at once)
                                                  Python: majority and agreement
```

Why parallel: the five reviewers are independent, so five calls take about as long as
one. `timing` in the response shows it: `review_wall_seconds` is the real time,
`review_sum_seconds` is what it would have taken one after another.

## Where this comes from

Anthropic's claude-cookbooks, folder `patterns/agents`:
https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents

- `basic_workflows.ipynb`, parallelization section: a `parallel()` helper that runs one
  prompt over a list of inputs on a thread pool with a worker cap, returning results in
  input order. Its example analyses market changes for four stakeholder groups at once.
  `parallel.py` here follows that shape.
- `util.py`: `llm_call()` and `extract_xml()` (see `llm.py`).
- Background: https://www.anthropic.com/engineering/building-effective-agents
  names the two forms of parallelization used here: sectioning (independent subtasks)
  and voting (the same task several times).

Written for this project (not from the cookbook): the reviewer panel and its prompts,
the aggregation step, voting, failure isolation (one failed call does not lose the
others), the timing report, the FastAPI service, the tests, and the Terraform.

## Files

| File | Purpose |
|---|---|
| `parallel.py` | `parallel_map()`: thread pool, input order kept, errors isolated. Start here. |
| `review.py` | Sectioning: reviewer panel, verdict logic, summary |
| `vote.py` | Voting: majority of N independent answers |
| `llm.py` | `llm_call()` and `extract_xml()` |
| `main.py` | FastAPI: `/health`, `/reviewers`, `/review`, `/vote` |
| `cli.py` | Run both patterns from the terminal |
| `samples/design.md` | A design with deliberate flaws to review |
| `tests/test_parallel.py` | 15 tests with a fake model; no API key needed |
| `Dockerfile`, `infra/main.tf` | Container and AWS ECS Fargate + load balancer |

## 1. Run the tests (no API key)

```
pip install -r requirements-dev.txt
python -m pytest -q
```

One test uses a barrier that only opens when all five reviewers are running at the same
moment, so it fails if the calls ever become sequential.

## 2. Run locally

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_anthropic_key

python cli.py review samples/design.md
python cli.py review samples/design.md --reviewers security cost
python cli.py vote samples/design.md "Is a credential stored in the repository?" --votes 5

uvicorn main:app --reload --port 8000
python3 -c 'import json; print(json.dumps({"design": open("samples/design.md").read()}))' | \
  curl -X POST http://localhost:8000/review -H "Content-Type: application/json" -d @-
curl -X POST http://localhost:8000/vote -H "Content-Type: application/json" \
  -d '{"text": "We store the API key in a config file in git.", "question": "Is a secret stored in version control?", "votes": 5}'
```

Review verdicts: `approve`, `changes_requested` (some reviewer has concerns), `blocked`
(some reviewer says do not ship). `complete: false` means a reviewer failed and its area
was not covered; the summary says so.

Settings (environment variables): `MODEL` (default `claude-sonnet-4-5`, reviewers and
summary), `FAST_MODEL` (default `claude-haiku-4-5`, votes), `MAX_WORKERS` (default 5).
If a model name is not available to your account, set the variable to one you can use.

Parallel calls count against your API rate limits at the same moment. If you see
rate-limit errors, lower `MAX_WORKERS`.

## 3. Docker

```
docker build -t agentic-parallel:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_anthropic_key agentic-parallel:latest
```

## 4. Deploy to AWS (ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-parallel --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-parallel:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-parallel:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-parallel:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-parallel/anthropic-key --secret-string 'your_anthropic_key'

cd infra
terraform init
terraform plan
terraform apply
```

Terraform prints `app_url`. Wait 2 to 3 minutes for the target to turn healthy; if it does
not, read CloudWatch log group `/ecs/agentic-parallel`.

```
curl http://<app_url>/reviewers
```

## 5. Clean up

```
cd infra
terraform destroy
```

The secret and the ECR repository were created by CLI; delete them separately if not needed.

## Exercises

1. Add a `compliance` reviewer: one entry in `REVIEWERS`. Run the review and compare `review_wall_seconds` with six reviewers.
2. Set `MAX_WORKERS=1` and compare the timing with the default.
3. Change `/vote` to use the main model and compare how often the votes agree.
4. Make the verdict stricter: block when the total `high_count` across reviewers is 3 or more.
