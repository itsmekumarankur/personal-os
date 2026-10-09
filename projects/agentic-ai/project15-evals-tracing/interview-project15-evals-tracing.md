# Architect Interview — Chapter 15: Evals and Tracing

**Role:** *Principal Architect, AI Platform* at a bank. Your team ships a loan-assistant agent weekly. I'm the interviewer.
**How to use:** answer aloud (60–90s), compare, score 0/1/2.
Legend: 🎯 intent · ✅ strong answer · 🔁 follow-up · 🚩 red flag

---
## ROUND 1 — Why measure at all

### Q1. A developer says: "I tried 10 prompts by hand and the new version feels better." What's your response as the architect?
🎯 Do you replace vibes with a process?
✅ Hand-testing is anecdote: small sample, biased toward recent cases, no baseline, not repeatable. Need a **fixed case set**, graders with pass/fail rules, run old vs new, compare with a gate in CI. Keep adding real production failures to the set (regression library).
🚩 "Let's collect user feedback" as the only answer.

### Q2. Evals vs tracing: what question does each answer, and why does the platform need both?
✅ Evals (offline, before shipping): "Is B better or worse than A on a known set?" Tracing (online, every request): "What did the agent do on THIS request, how long, how much?" Evals tell you **if** it got worse; traces tell you **why**. They share one idea: the **trace is the evidence** — graders read the same spans production emits.

---
## ROUND 2 — Tracing design

### Q3. Define trace and span. Draw the trace of one request that calls the model, a tool, then the model again.
✅ Trace = story of one request; span = one step with start, end, parent, attributes, status. `agent.run` → `chat` (tokens, cost) → `execute_tool` → `chat`. Attributes follow OpenTelemetry GenAI conventions (still marked experimental upstream, so verify before wiring a vendor). Exceptions mark the span ERROR and propagate to parents.

### Q4. You hand work to a thread pool and the child spans show up as separate, orphaned traces. Why?
🎯 Real instrumentation pain.
✅ Context is stored in a `ContextVar`; **threads don't inherit it**. Capture a snapshot and run the work inside that context (`ctx.run`), or pass the span explicitly. Same issue across async tasks in some frameworks and across processes — which is why `traceparent` exists.

### Q5. Service A (orchestrator) calls Service B (advisor). How do you get ONE trace?
✅ Propagate `traceparent: 00-<trace-id>-<parent-span-id>-01`; B starts its spans under that parent. Mention sampling flag, and that B must not trust a caller's header blindly for security decisions (it's only a correlation id).

### Q6. You process millions of requests. Head sampling or tail sampling? Defend.
🎯 Trade-off thinking.
✅ Head: decide at the start; cheap but may discard the one trace you needed. Tail: decide at the end; can keep **all errors and all slow traces** plus a share of normal ones; price is memory/buffering of unfinished traces and complexity. Recommended here: keep a percentage of ordinary traces, always keep errors and slow ones.
🔁 "What breaks tail sampling in a multi-service trace?" → all spans of a trace must reach the same decision point.

### Q7. Your security team asks: "Are prompts and answers in the trace store?" Design the policy.
✅ A trace store is a **second copy of customer conversations**. Modes: off / hash / truncate (default, redacted) / full (redacted). Mask card numbers (Luhn-checked), API keys, emails. Decide before sending to a vendor; retention, access control, regional residency, deletion on request.
🚩 "We'll log everything, it's for debugging."

### Q8. The cost on your dashboard says $0 for a new model. What happened and what design prevents it?
✅ Missing price → silent zero. The platform **raises on an unknown model** instead of defaulting to zero. Prices are placeholders in config, updated from the pricing page; include cache read/write in the arithmetic; reconcile with the invoice monthly.

---
## ROUND 3 — Eval design

### Q9. Explain the "grader ladder". Which graders do you write first and why?
✅ Cheap/exact/stable → costly/flexible/noisy: contains/regex/number_close (look at the **answer**) → tool_called, max_llm_calls, cost caps (look at the **trace**) → LLM judge. Start low on the ladder; use a judge only where code can't decide (tone, helpfulness). A case passes only if **all** its graders pass.

### Q10. Why grade the trace and not only the answer?
🎯 The chapter's sharpest insight.
✅ A degraded model can guess without calling the tool and sometimes be right by luck; the answer check passes, but the behaviour is wrong. Also, a right answer reached with 4 model calls instead of 2 is a cost regression (the "chatty" agent). Trace graders catch process failures.

### Q11. In the lab, the "degraded" agent was cheaper and faster than the good one but much worse. What does it teach?
✅ **Cost and latency alone would have shipped it.** A gate must combine quality with cost/latency; improvements in one metric can hide collapse in another.

### Q12. You want an LLM judge. What can go wrong and what rails do you add?
✅ Judge is a model grading a model: bias, inconsistency, prompt injection from the answer being graded, position bias, self-preference. Rails: put the answer inside data tags and neutralise tag text; unreadable verdict → retry once → **fail**, never silent pass; **calibrate** against human labels (accuracy, **Cohen's kappa**, and the **false-pass rate** — judge says pass, human says fail, the dangerous direction); pairwise with swapped order (if verdict flips = position bias = tie); use a different model family for judging when possible.
🔁 "Accuracy was 90%. Good?" → depends on class balance; look at kappa and false-pass rate.

### Q13. A case passes 3 of 5 runs. What is it, and what do you do?
✅ **Flaky** — a finding itself. Use repeats; report pass-rate per case; investigate non-determinism (temperature, tool ordering, timing); decide whether to count flaky as failure for critical cases.

---
## ROUND 4 — Comparing runs and shipping

### Q14. Explain gate vs noise. Why do you need both?
🎯 Statistical honesty.
✅ **Gate** = fixed rules agreed in advance (pass rate may not drop >3 points; no critical case regresses; cost +25% max; p95 latency +30% max; same cases in both runs) → deterministic CI decision. **Noise** = how much to believe the difference: sign test on cases that changed, bootstrap interval. With 12 cases one flip is ~8 points. Example: `fake-chatty` drops 2 cases, sign-test p=0.5 (could be luck), yet the gate fails it because cost and latency rose. Two different questions; print both.

### Q15. Eval set has 12 cases. Your VP wants to claim "+5% improvement". Respond.
✅ Not significant; increase and diversify cases (by category, difficulty, adversarial), include production samples, report confidence intervals, stratify by category, avoid tuning prompts to the eval set (overfitting), keep a hidden holdout.

### Q16. Which cases are "critical" and why can't the average hide a regression there?
✅ Safety/compliance cases (e.g. never reveal other customers' data, refuse unsafe actions). Any regression blocks release regardless of overall score. Average-based gates let one catastrophic failure hide among many passes.

---
## ROUND 5 — Curveballs
### Q17. Tracing must never break a request. How is that guaranteed?
✅ Exporters swallow errors, are async/batched with bounded queues, drop on overflow, time-limited; test with a failing collector.
### Q18. How do you use production traces to improve the eval set?
✅ Sample failures/low-feedback/slow traces → human label → turn into cases with graders; track "eval coverage" of real traffic categories.
### Q19. Offline evals pass, production quality drops. Why?
✅ Distribution shift, stale dataset, tool/data changes, model-provider drift, prompt injection, judge drift; add online monitoring (guardrail trip rate, user feedback, tool error rate) and canary releases.

---
## RAPID FIRE
1. What carries trace context across services? 2. Why keep all error traces? 3. What does an unknown model price do here? 4. What's Cohen's kappa for? 5. What's a false pass? 6. What does `--repeats` expose? 7. Name two trace graders. 8. Why swap A/B in pairwise judging? 9. Which cases may never regress? 10. Why is the exporter fail-safe?

*(Answers: `traceparent` · they're the ones you need · raises · agreement beyond chance · judge pass, human fail · flakiness · tool_called, max_llm_calls · detect position bias · critical cases · tracing must not break requests)*

## HANDS-ON CHALLENGE
Run `evalctl.py run` for `fake-good`, `fake-degraded`, `fake-chatty`; run `compare` and `gate`. Explain, for each of the three, which rule fires and whether the sign test agrees.

## SCORECARD
30–38 architect-ready · 22–29 revisit judge calibration and gate-vs-noise · <22 redo the lab and README sections 4–6.
*Honest note: the real-model path and a real tracing backend were not run in the lab; GenAI attribute names are experimental — check before adopting.*
