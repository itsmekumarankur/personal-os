# Project 5: Parallelization — Design Review and Voting

## 1. What Is Parallelization?

Parallelization means **running multiple AI model calls at the same time** instead of one after another.

This project demonstrates two patterns:

1. **Sectioning:** Multiple AI reviewers check a design from different perspectives.
2. **Voting:** Multiple AI calls answer the same Yes/No question, and Python decides the majority.

Both patterns use a common helper function to run tasks in parallel.

## 2. How Does It Work?

### A. Sectioning — AI Design Review Panel

**Goal:** Review a software design from different perspectives.

```text
         Software Design
                |
                v
       +--------+--------+
       |        |        |
       v        v        v
   Security  Reliability Performance
       |        |        |
       +--------+--------+
                |
      +---------+----------+
      |         |          |
      v         v          v
     Cost  Maintainability
                |
                v
       Python combines reviews
       (worst verdict wins)
                |
                v
       One AI call writes
       the final summary
```

**In simple words:**

- Five independent reviewers examine the same design.
- Each reviewer focuses on one area, such as security or performance.
- Python combines their findings and applies the verdict rule.
- One final AI call writes a summary of the review.

### B. Voting — Multiple AI Answers

**Goal:** Get multiple independent answers to the same question.

```text
       Text + Yes/No Question
                  |
         +--------+--------+
         |        |        |
         v        v        v
       Vote 1   Vote 2   Vote 3
         |        |        |
         +--------+--------+
                  |
          +-------+-------+
          |               |
          v               v
        Vote 4          Vote 5
          |               |
          +-------+-------+
                  |
                  v
          Python counts votes
                  |
                  v
       Majority + Agreement
```

**In simple words:**

- Five independent model calls answer the same question.
- Each call returns a Yes or No.
- Python counts the votes and identifies the majority.
- Python also calculates how much the answers agree with one another.

## 3. Why Run Calls in Parallel?

Imagine five reviewers each take 4 seconds to complete their review.

| Execution method | Approximate time |
|---|---:|
| One after another | 20 seconds |
| All at the same time | 4 seconds |

Actual execution time depends on model latency, network delays, and system resources.

The project reports two timing measurements:

- `review_wall_seconds`: Actual elapsed time for the parallel operation.
- `review_sum_seconds`: Sum of the execution times of all individual calls.

**Key learning:** Parallel execution can reduce waiting time when tasks are independent.

## 4. Project Files and Their Responsibilities

| File | Purpose |
|---|---|
| `parallel.py` | Runs multiple tasks concurrently using `parallel_map()`. Preserves input order and isolates errors. Start here. |
| `review.py` | Implements sectioning: reviewer panel, verdict logic, and final summary. |
| `vote.py` | Implements voting: collects independent answers and calculates the majority. |
| `llm.py` | Contains `llm_call()` to call the model and `extract_xml()` to extract structured output. |
| `main.py` | Provides FastAPI endpoints: `/health`, `/reviewers`, `/review`, and `/vote`. |
| `cli.py` | Allows you to run both patterns from the terminal. |
| `samples/design.md` | Contains a deliberately flawed software design for review. |
| `tests/test_parallel.py` | Contains 15 tests using a fake model, so no API key is required. |
| `Dockerfile` | Defines how to package the application into a container. |
| `infra/main.tf` | Defines AWS infrastructure, including ECS Fargate and a load balancer. |

## 5. What Should an AI Architect Learn From This Project?

- **Parallel execution:** How to run independent model calls concurrently.
- **Agent collaboration:** How specialized reviewers can contribute to one result.
- **Deterministic orchestration:** Python applies explicit rules to combine model outputs.
- **Fault isolation:** One task's failure should not unnecessarily break other tasks.
- **Performance measurement:** Compare actual elapsed time against the sum of individual execution times.
- **Scalability:** Understand thread pools, concurrency limits, model API rate limits, and infrastructure costs.

**Remember:** The AI models perform the reviews or make individual decisions. Python coordinates the calls, combines the results, and applies the final decision rules.