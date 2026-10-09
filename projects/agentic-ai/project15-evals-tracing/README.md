# Project 15: Evals and tracing platform

**The idea in one line:** an agent is not finished when it works once. It is finished when you can *measure* that it works,
*see* what it did on every request, and *stop a bad change* before it ships.

Two halves:

| Half | Question it answers | Tool here |
|---|---|---|
| **Tracing** | "What did the agent do on THIS request, how long did each step take, what did it cost?" | `tracing.py`, `/traces` API, ASCII waterfall |
| **Evals** | "Is version B better or worse than version A, on a fixed set of questions?" | `evals/cases.jsonl`, `runner.py`, `compare.py`, `evalctl.py gate` |

No API key is needed. Fake models play a good, a degraded and a wasteful agent so you can watch the platform catch each one.

## 0. Run it in 2 minutes

```bash
pip install -r requirements-dev.txt
python -m pytest -q                                     # 67 tests

python evalctl.py run --agent fake-good     --out runs/good.json
python evalctl.py run --agent fake-degraded --out runs/bad.json
python evalctl.py run --agent fake-chatty   --out runs/chatty.json

python evalctl.py compare runs/good.json runs/bad.json  # prints the comparison
python evalctl.py gate    runs/good.json runs/bad.json  # same, but exit code 1 = "do not ship"
python evalctl.py trace   runs/good.json emi_5y         # the ASCII waterfall of one request
python evalctl.py report  runs/bad.json --baseline runs/good.json --out report.html
python evalctl.py calibrate                             # how far can you trust the judge?

DEMO_FAKE=1 uvicorn main:app_factory --factory --port 8000
curl -s localhost:8000/ask -H 'content-type: application/json' -d '{"question":"What is the late payment fee?"}'
curl -s localhost:8000/traces ; curl -s localhost:8000/stats
```
For a real model: `export ANTHROPIC_API_KEY=...` and use `--agent anthropic --judge anthropic` (not run by me, see section 9).

## 1. The big picture

```
                          EVALS (offline, before you ship)                         TRACING (online, every request)

 cases.jsonl --> runner --> agent under test --+--> answer                     request --> agent.run
 (questions +      |             |             |                                              |- chat       (tokens, cost)
  graders)         |             +-- spans ----+--> trace                                      |- execute_tool
                   v                                                                           `- chat
              graders look at:                                                                     |
              1. the answer                                                              exporters: memory / jsonl / OTLP
              2. the trace (tools, calls, cost, time)                                              |
              3. a judge model (only if code cannot)                                      Jaeger / Tempo / Datadog / ...
                   |
                   v
              run1.json  ---+
                            +--> compare --> GATE (fixed rules) + NOISE (sign test, interval) --> ship / do not ship
              run2.json  ---+
```
The two halves share one idea: **the trace is the evidence.** The eval graders read the same spans that production emits, so
"the agent made 4 model calls instead of 2" is a testable fact, not a feeling.

## 2. Tracing: the words

```
 trace  = the story of ONE request
 span   = one step in it (has start, end, parent, attributes, status)

 agent.run ................................ 637 ms
 |- chat demo-model ....................... 317 ms   in=63 out=25  $0.00056
 |- execute_tool calculate_emi ............   0 ms
 `- chat demo-model ....................... 320 ms   in=81 out=19  $0.00053
```
* **Context** is "which span am I inside?". It lives in a `ContextVar`, so two requests at once never mix. *Threads do not inherit it*:
  use `ctx = tracer.snapshot(); pool.submit(ctx.run, fn)` or the child span becomes an orphan (a test shows exactly this).
* **Attributes** follow the OpenTelemetry GenAI names (`gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.tool.name`).
  Those names are still marked experimental upstream. Check them before wiring a real backend.
* **Status**: an exception marks the span `ERROR` and the error travels up to the parents.

### Sampling: you cannot keep everything
```
 head sampling  decide at the START of the request   cheap, but you may throw away the one trace you needed
 tail sampling  decide at the END                    you can say "keep every error and every slow trace"
```
Here: keep a share (`TRACE_SAMPLE_RATE`) of ordinary traces, and **always** keep errors and traces slower than `TRACE_SLOW_MS`.
The price of tail sampling is memory: spans of an unfinished request wait in a buffer until the request ends.

### Prompts are sensitive
`TRACE_CONTENT` = `off` (store nothing), `hash` (store a fingerprint), `truncate` (default: redacted and cut), `full` (redacted).
Card numbers (Luhn-checked), API keys and e-mail addresses are masked in every mode except `off` and `hash`.
Decide this *before* you point traces at a vendor: a trace store is a second copy of your customer conversations.

### Crossing services: `traceparent`
When service A calls service B, A sends `traceparent: 00-<trace id>-<parent span id>-01`. B starts its spans under that parent, so
one request shows up as one trace across both. `POST /ask` accepts the header (a test proves the trace joins). Project 16 uses this.

### Getting data out
`to_otlp()` produces OTLP/JSON, which collectors accept at `POST /v1/traces`. `OtlpHttpExporter` does the POST and swallows errors
(**tracing must never break a request**). I tested it against a mock, not a real collector.

## 3. Cost: the arithmetic
`cost = tokens / 1,000,000 x price per million`, summed for input, output, cache reads and cache writes.
`pricing/pricing.json` holds **placeholder prices**. Copy current numbers from the Anthropic pricing page. An unknown model *raises*:
a silent zero would make the dashboard say "free" for a model you forgot to price.

## 4. Evals: the grader ladder
```
 cheap, exact, stable                                                       costly, flexible, noisy
 contains / regex / number_close   tool_called / max_llm_calls / ...   llm_judge
 (look at the ANSWER)              (look at the TRACE)                 (a model grades a model)
```
* A case passes only if **every** grader passes. A run with a right answer but 4 model calls instead of 2 fails (`fake-chatty` shows it).
* **Why trace graders:** the degraded model guesses without calling the tool. Some guesses are right by luck. The answer check alone misses it.
* **Critical cases** (the three safety cases) may never regress, whatever the average says.
* **Repeats:** `--repeats 5` runs each case 5 times. A case that passes 3 of 5 is **flaky**, which is a finding by itself.

## 5. The judge, and why you must not trust it blindly
A judge model is a model grading another model. It is the only way to check things like tone, and it is wrong in known ways.
```
 answer ---> [ judge prompt: question + rubric + <answer>DATA</answer> ] ---> <score>1-5</score>
```
Rails in `judge.py`:
1. The answer is inside `<answer>` tags, told to be data, and tag text inside the answer is neutralised (a test tries to break out).
2. An unreadable verdict is retried once, then **fails**. It never silently passes.
3. **Calibrate**: `evalctl.py calibrate` compares the judge with 12 human labels: accuracy, **Cohen's kappa** (agreement beyond luck),
   and the **false-pass rate** (judge says pass, human says fail: the dangerous kind). Do this before you trust any judge. The built-in
   `HeuristicJudge` is a stand-in with rules, and it disagrees with the humans on purpose so you can see what a bad judge looks like.
4. **Pairwise** with the order swapped: if the verdict flips when you swap A and B, that is *position bias*, and the result is a tie.
5. Use a different model for judging than for generating when you can (models like their own style).

## 6. Comparing runs: gate versus noise
```
 GATE  (fixed rules, agreed in advance, deterministic, used by CI)
   pass rate may not drop more than 3 points      | any category may not drop more than 10 points
   no critical case may regress                   | cost per run may not rise more than 25%
   p95 latency may not rise more than 30%         | both runs must contain the same cases

 NOISE (tells you how much to believe the difference)
   sign test:  of the cases that CHANGED, how lopsided is the split?   8 better / 2 worse  ->  p = 0.109
   bootstrap:  resample the per-case differences -> a 95% interval
```
With 12 cases one flip is 8 points. The `fake-chatty` run drops 2 cases and the sign test says **p = 0.5: could be luck**,
yet the gate still fails it, because cost and latency also rose. Two different questions, two different answers. Print both.
Also note `fake-degraded` is **cheaper and faster** than `fake-good` and much worse: **cost and latency alone would have shipped it.**

## 7. Files
| File | What it is |
|---|---|
| `tracing.py` | spans, context, sampling, redaction, traceparent, exporters, OTLP, ASCII waterfall |
| `pricing.py` | cost arithmetic and per-trace totals |
| `agent.py`, `tools.py` | the agent under test (bank support bot), traced |
| `demo_fake.py` | fake models (good / degraded / chatty) and a stand-in judge |
| `graders.py` | answer, trace and judge graders |
| `judge.py` | judge prompt, parsing, pairwise, calibration |
| `runner.py` | run all cases (threads, repeats), save one JSON per run |
| `compare.py`, `stats.py` | gate, sign test, bootstrap, kappa, percentiles |
| `report.py`, `evalctl.py` | HTML report, command line |
| `main.py` | HTTP service: `/ask`, `/traces`, `/traces/{id}`, `/traces/{id}/otlp`, `/stats` |
| `evals/cases.jsonl` | 12 cases (math, fees, safety, chat); `calibration/human_labels.jsonl` 12 labels |

## 8. Read the code in this order
1. `tracing.py` `Tracer.span` and `_finish` (how a tree of spans is built, and the keep-or-drop decision)
2. `agent.py` (where the spans are created)
3. `graders.py` then `runner.py` `_one`
4. `compare.py`
5. the tests, then break something. Three that I did: removed the "always keep errors" rule (a test failed), made an unreadable
   judge reply count as a pass (two tests failed), removed the critical-regression check (a test failed).

## 9. What I did not verify
* Not run against the live Anthropic API, a real OTLP collector, Docker or AWS. Fake models and mocks only.
* The fake models behave the way I wrote them. Real models fail in less tidy ways, so expect to rewrite cases and graders after your first real run.
* 12 cases is a demo. Real suites need 100+ cases, drawn from real traffic, with a hold-out set.
* The heuristic judge is not a judge. Calibrate a real one against human labels you wrote.
* Prices are placeholders. OpenTelemetry GenAI attribute names may have changed.
* The in-memory trace store loses data on restart and is per instance. A real deployment exports to a trace backend.
* No authentication on the API (Project 10 shows how).

## 10. Exercises
1. Add a case where the user asks for an EMI with no tenure. What should the agent do? Write the grader first.
2. Add a `max_cost_usd` grader to every math case and watch which model fails it.
3. Run `--repeats 5` with a model that sometimes errors. Find the flaky case in the report.
4. Add a second judge and measure how often the two judges disagree (a pairwise test with swapped order).
5. Turn `TRACE_CONTENT=off`, ask a question with a card number, and prove (with a test) that nothing leaks.
6. Add a `p99` column to the report and explain why 12 runs cannot support it.
7. Point `OtlpHttpExporter` at a local Jaeger (`docker run -p 4318:4318 -p 16686:16686 jaegertracing/all-in-one`) and find your trace. Tell me what broke.
