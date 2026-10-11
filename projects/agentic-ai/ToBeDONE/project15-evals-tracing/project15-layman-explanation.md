# Project 15 — Evals and Tracing in Very Simple Terms

Think of a **school**.

An AI agent that "seemed to work when I tried it" is a student who answered one question correctly. That tells you nothing. A school needs two things:

- **Exams (evals):** the same fixed set of questions every time, marked by clear rules. So you can say "this year's batch scored better or worse than last year's".
- **A CCTV and logbook (tracing):** a record of what the student actually *did* on each question: which books they opened, how long they took, how much it cost.

Evals tell you **if** something got worse. Tracing tells you **why**.

---

## What Project 15 teaches

1. **"It worked once" is not evidence.** Keep a fixed list of test questions with expected behaviour, and run every new version against it.
2. **Judge the journey, not only the answer.** The graders also look at the trace: did it call the right tool? Did it call the model 4 times when 2 was enough? Did it cost double? A correct answer reached wastefully is still a regression.
3. **A comparison needs a gate.** Rules like "accuracy must not drop" and "cost must not rise more than X%" produce a clear ship / don't-ship result, usable in your deployment pipeline.
4. **Beware of noise.** Scores wobble. A small difference on few questions may be luck. The project uses a simple statistical check so you don't celebrate (or panic over) random movement.
5. **Using an AI as the marker is useful but must be checked.** First use plain code to mark whatever code can mark. Use an AI judge only for the rest, and *test the judge* against human-marked examples to see how far it can be trusted.
6. **A trace is a story of one request.** Each step is a "span" with start, end, parent, tokens and cost. A waterfall view shows where time and money went.
7. **You can't keep every trace.** Deciding up front loses the one you needed; deciding at the end lets you say "keep every error and every slow request".
8. **Tracing context can get lost across threads.** If you hand work to another thread without passing the context, its steps become orphans on the trace.

---

## Why do we need it?

Agents change constantly: a prompt tweak, a new model, a new tool. Without exams and a logbook, every change is a gamble and every incident is a mystery. This is what lets a team change an agent **with confidence**.

## The one-sentence takeaway

> If you can't measure it and can't see what it did, you can't safely improve it.

**Honest limit:** the agents are fake (a good one, a degraded one, a wasteful one) so the platform can be shown catching each. The real-model path and a real tracing backend were not run.
