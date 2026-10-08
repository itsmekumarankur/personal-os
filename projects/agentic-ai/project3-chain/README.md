# Project 3: Prompt Chaining (draft -> critique -> polish)

A workflow, not an agent: the steps and their order are fixed in code. Each step
is one Claude call, and later steps see the outputs of earlier ones. A plain
Python check (the "gate") decides whether the last step runs.

```
request -> [1 draft] -> [2 critique + verdict] -> gate -> [3 polish] -> final
                                                   |
                                      verdict "pass" -> return the draft (2 calls)
```

## Where this comes from

Anthropic's claude-cookbooks, folder `patterns/agents`:
https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents

- `util.py`: `llm_call()` and `extract_xml()` are adapted from here
  (changes: client created on first use so tests need no API key; temperature is a parameter).
- `basic_workflows.ipynb`: the prompt-chaining pattern, where each step's output feeds the next.
- Background reading: https://www.anthropic.com/engineering/building-effective-agents
  (prompt chaining, and the programmatic "gate" between steps).

Written for this project (not from the cookbook): the three prompts, the context
that carries the request plus earlier outputs, per-step temperature, the gate,
the FastAPI service, the tests, and the Terraform.

## Files

| File | Purpose |
|---|---|
| `chain.py` | The pipeline. Start reading here. |
| `main.py` | FastAPI: `GET /health`, `POST /write` |
| `cli.py` | Run the chain in a terminal and print every step |
| `tests/test_chain.py` | 6 tests with a fake model; no API key needed |
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

python cli.py "Explain what a load balancer does" --audience "new engineers" --max-words 150

uvicorn main:app --reload --port 8000
curl -X POST http://localhost:8000/write \
  -H "Content-Type: application/json" \
  -d '{"task": "Explain what a load balancer does", "audience": "new engineers", "max_words": 150}'
```

The response has `draft`, `critique`, `verdict`, `final` and `steps_run`
(3 normally, 2 when the critic says "pass").

Optional: set `MODEL` to use a different Claude model (default `claude-sonnet-4-5`).

## 3. Docker

```
docker build -t agentic-chain:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_anthropic_key agentic-chain:latest
```

## 4. Deploy to AWS (ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-chain --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-chain:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-chain:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-chain:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-chain/anthropic-key --secret-string 'your_anthropic_key'

cd infra
terraform init
terraform plan
terraform apply
```

Terraform prints `app_url`. Wait 2 to 3 minutes for the target to turn healthy;
if it does not, read CloudWatch log group `/ecs/agentic-chain`.

```
curl http://<app_url>/health
curl -X POST http://<app_url>/write -H "Content-Type: application/json" \
  -d '{"task": "Write a short note announcing a Friday release freeze", "audience": "engineering team"}'
```

The load balancer idle timeout is set to 120 s because three model calls run one after another.

## 5. Clean up

```
cd infra
terraform destroy
```

The secret and the ECR repository were created by CLI; delete them separately if not needed.

## Exercises

1. Add a fourth step (for example "check tone against the audience") and watch `steps_run` change.
2. Make the gate stricter: add a word-count check in Python and re-run polish if the draft is over `max_words`.
3. Compare the final text with and without the critique step to see what the chain adds.
