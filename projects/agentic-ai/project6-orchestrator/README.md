# Project 6: Orchestrator-Workers

A lead model reads a goal and **decides the subtasks itself**. Workers do them at the same
time. A last call merges the results into one answer.

```
goal --> [ORCHESTRATOR] --> plan: task 1, task 2, ... task N     (N is decided by the model)
                                   |      |            |
                                   v      v            v
                              [worker] [worker] ... [worker]     (all at once)
                                   \      |            /
                                    v     v           v
                                   [SYNTHESIZER]  --> one final answer (gaps listed if a worker failed)
```

**Difference from Project 5.** In Project 5 the five reviewers were fixed by us. Here the
model chooses how many parts there are and what they are. Use this when you cannot list the
subtasks in advance (a plan, a research question, a change that touches unknown files).
If you can list them in advance, Project 5 is simpler and safer.

## Where this comes from

Anthropic's claude-cookbooks, folder `patterns/agents`:
https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents

- `orchestrator_workers.ipynb`: the `FlexibleOrchestrator` class. The orchestrator replies
  with `<analysis>` and `<tasks>`, each task becomes one worker call, and each worker replies
  inside `<response>`. `orchestrator.py` follows this shape.
- `util.py`: `llm_call()` and `extract_xml()` (see `llm.py`).
- Background: https://www.anthropic.com/engineering/building-effective-agents
  (the "orchestrator-workers" workflow).

Written for this project (not from the cookbook): treating the plan as untrusted output (regex
parsing, a cap on the number of tasks, a one-task fallback), running workers in parallel with
failure isolation, showing each worker only the titles of the other tasks, the synthesis step
with a "Gaps" rule, timing, the FastAPI service, tests, and Terraform.

## Files

| File | Purpose |
|---|---|
| `orchestrator.py` | `make_plan`, `run_worker`, `synthesize`, `orchestrate`. Start here. |
| `parallel.py` | `parallel_map()` from Project 5 |
| `llm.py` | `llm_call()` and `extract_xml()` |
| `main.py` | FastAPI: `/health`, `/orchestrate` |
| `cli.py` | Run from the terminal and see the plan |
| `samples/goal.md` | A sample goal |
| `tests/test_orchestrator.py` | 15 tests with a fake model; no API key needed |
| `Dockerfile`, `infra/main.tf` | Container and AWS ECS Fargate + load balancer |

## 1. Run the tests (no API key)

```
pip install -r requirements-dev.txt
python -m pytest -q
```

One test uses a barrier that only opens if all three workers run at the same moment.

## 2. Run locally

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_anthropic_key

python cli.py samples/goal.md
python cli.py samples/goal.md --max-tasks 3

uvicorn main:app --reload --port 8000
python3 -c 'import json; print(json.dumps({"goal": open("samples/goal.md").read(), "max_tasks": 4}))' | \
  curl -X POST http://localhost:8000/orchestrate -H "Content-Type: application/json" -d @-
```

Run it twice with different goals and look at the plan. The number and names of the tasks change.
That is the point of the pattern.

Settings (environment variables): `MODEL` (default `claude-sonnet-4-5`, used by the
orchestrator and the synthesizer), `WORKER_MODEL` (default `claude-haiku-4-5`, used by workers).
If a model name is not available to your account, set the variable to one you can use. For better
worker quality, set `WORKER_MODEL` to the same value as `MODEL`.

## 3. What to take care of

- **The plan is model output, so it is untrusted.** The code caps the task count
  (`max_tasks`, never more than `HARD_MAX_TASKS = 8`), ignores tasks with no description, and
  falls back to one task if nothing usable comes back. The response says `fallback: true` or
  `truncated: true` when this happened.
- **Cost is `1 + N + 1` calls**, and N is chosen by the model, so the cap is your cost control.
- **Workers are blind to each other.** They see only the titles of the other tasks, so their
  answers can overlap or disagree. The synthesizer is where that gets cleaned up, so check it.
- **A failed worker does not stop the request.** The answer comes back with `complete: false`
  and a "Gaps" section. If every worker fails, you get a 502.
- **Time is plan + slowest worker + synthesis**, three steps one after another. The load
  balancer idle timeout is set to 120 seconds for this reason.

## 4. Docker

```
docker build -t agentic-orchestrator:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_anthropic_key agentic-orchestrator:latest
```

## 5. Deploy to AWS (ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-orchestrator --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-orchestrator:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-orchestrator:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-orchestrator:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-orchestrator/anthropic-key --secret-string 'your_anthropic_key'

cd infra
terraform init
terraform plan
terraform apply
```

Terraform prints `app_url`. Wait 2 to 3 minutes for the target to turn healthy; if it does
not, read CloudWatch log group `/ecs/agentic-orchestrator`. There is no login and only HTTP.
Delete the stack when you finish.

## 6. Clean up

```
cd infra
terraform destroy
```

The secret and the ECR repository were created by CLI; delete them separately if not needed.

## Exercises

1. In `ORCHESTRATOR_SYSTEM`, change "between 2 and N" to "exactly 3". Does the model obey? What does the cap do if it does not?
2. Set `WORKER_MODEL` equal to `MODEL` and compare the quality of the final answer.
3. Give workers the full descriptions of the other tasks. Do the answers overlap less, or does the cost go up?
4. Make a second round: if the synthesizer lists a Gap, run one more worker for it (this leads toward Project 8).
