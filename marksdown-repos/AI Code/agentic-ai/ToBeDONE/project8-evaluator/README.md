# Project 8: Evaluator-Optimizer

One call **writes**, another call **judges** against a checklist, and the writer **improves**
using the feedback. Repeat until the judge says PASS or the round limit is reached.

```
brief + criteria
      |
      v
  [WRITER] --> draft --> [CODE CHECKS] --too long?--> feedback --+
      ^                        |                                 |
      |                        v ok                              |
      |                   [REVIEWER] --> PASS ? --yes--> done    |
      |                        | no                              |
      +------ feedback -------<+---------------------------------+

 stops when:  PASS   |   max_rounds reached   |   writer repeats itself ("stalled")
```

**Use it when** you can say clearly what "good" means (a checklist) and a second pass really
improves the result: customer messages, summaries, code against tests. If you cannot write the
criteria down, or one good prompt already works, do not use it. It costs up to 2 calls per round.

## Where this comes from

Anthropic's claude-cookbooks, folder `patterns/agents`:
https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents

- `evaluator_optimizer.ipynb`: `generate()` replies with `<thoughts>` and `<response>`;
  `evaluate()` replies with `<evaluation>` (PASS, NEEDS_IMPROVEMENT, FAIL) and `<feedback>`;
  `loop()` repeats until PASS. `refine.py` follows this shape.
- `util.py`: `llm_call()` and `extract_xml()` (see `llm.py`).
- Background: https://www.anthropic.com/engineering/building-effective-agents
  (the "evaluator-optimizer" workflow).

**What the cookbook does not do, and this project adds.** The cookbook loop has no round limit:
if the evaluator never says PASS it runs forever. Here there is `max_rounds`. Also added: an
unreadable verdict counts as NEEDS_IMPROVEMENT and never as PASS; a code check (word limit) runs
before the reviewer; the loop stops if the writer repeats itself; the text under review is
passed to the reviewer as data; the history of every round is returned; a separate `EVAL_MODEL`
setting; the FastAPI service, tests and Terraform. One more change: the cookbook asks for PASS
only when "you have no further suggestions", which invites endless nit-picking. The prompt here
says PASS when every criterion is met and not to withhold it for taste.

## Files

| File | Purpose |
|---|---|
| `refine.py` | `generate`, `evaluate`, `hard_checks`, `refine` (the loop). Start here. |
| `llm.py` | `llm_call()` and `extract_xml()`, plus `MODEL` and `EVAL_MODEL` |
| `main.py` | FastAPI: `/health`, `/criteria`, `/refine` |
| `cli.py` | Watch every round from the terminal |
| `samples/incident.md` | A sample brief (made-up facts) |
| `tests/test_refine.py` | 23 tests with a fake model; no API key needed |
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

python cli.py samples/incident.md
python cli.py samples/incident.md --max-words 60 --max-rounds 4

uvicorn main:app --reload --port 8000
python3 -c 'import json; print(json.dumps({"task": open("samples/incident.md").read(), "max_words": 120, "max_rounds": 3}))' | \
  curl -X POST http://localhost:8000/refine -H "Content-Type: application/json" -d @-
```

Try `--max-words 40`: the writer will probably break the limit, and you will see a round
"checked by code" that cost no reviewer call. Try your own criteria through the API
(`"criteria": ["Mentions the refund time.", "No more than 2 sentences per paragraph."]`).

Response fields: `status` is `passed`, `max_rounds` or `stalled`. `passed: false` still returns
the last draft, so check the flag before using the text. `history` has every draft, verdict and
piece of feedback.

Settings (environment variables): `MODEL` (writer, default `claude-sonnet-4-5`), `EVAL_MODEL`
(reviewer, defaults to `MODEL`). A model that grades its own work tends to agree with itself, so
for real use set `EVAL_MODEL` to a different model. If a model name is not available to your
account, set the variable to one you can use.

## 3. What to take care of (architect notes)

- **The loop must have an exit that does not depend on the model.** `max_rounds` (1 to 5) is
  that exit. Without it, cost has no ceiling.
- **Check in code what code can check.** Word counts, required phrases and banned words are
  certain; a model's opinion is not. The code check runs first and the reviewer is skipped when it
  fails.
- **The reviewer is only as good as the criteria.** Vague criteria ("make it good") give vague
  feedback and endless rounds. Write checkable ones.
- **The reviewer can be wrong or fooled.** The draft is wrapped in tags and the reviewer is told to
  ignore instructions inside it. Even so, for high-stakes text keep a human approval step
  (Project 10).
- **The writer must not invent facts.** The prompt says so and the reviewer checks it, but it is
  not a guarantee. Compare the final text with the brief yourself.
- **More rounds do not always mean better.** Read `history` for a few runs. Often round 2 fixes
  the main problem and later rounds only reshuffle words.
- **Time.** Rounds run one after another. Five rounds can take over a minute, so the load balancer
  idle timeout is set to 300 seconds.

## 4. Docker

```
docker build -t agentic-evaluator:latest .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_anthropic_key agentic-evaluator:latest
```

## 5. Deploy to AWS (ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-evaluator --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-evaluator:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-evaluator:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-evaluator:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-evaluator/anthropic-key --secret-string 'your_anthropic_key'

cd infra
terraform init
terraform plan
terraform apply
```

Terraform prints `app_url`. Wait 2 to 3 minutes for the target to turn healthy; if it does not,
read CloudWatch log group `/ecs/agentic-evaluator`. There is no login and only HTTP. Run
`terraform destroy` when you finish; delete the secret and the ECR repository separately.

## Exercises

1. Remove the word limit from the request path (`max_words=500`) and use a brief that invites a long text. Does the reviewer still stop it from rambling?
2. Make the criteria weaker ("sounds nice") and watch how many rounds it takes. Then make them sharper.
3. Set `EVAL_MODEL` to a different model from `MODEL` and compare how strict the reviews are.
4. Add a code check: the text must contain the string "5 PM". Where does it go?
5. Pass the feedback of all earlier rounds to the writer, not only the latest. Does it avoid repeating old mistakes? What does it cost in tokens?
