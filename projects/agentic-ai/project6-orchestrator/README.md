# Project 6: Orchestrator-Workers

## 1. What Is Orchestrator-Workers?

This pattern uses one lead AI model to break a big goal into smaller tasks.

The lead model, called the **Orchestrator**, decides:
- What tasks need to be done.
- How many tasks are required.
- What each task should accomplish.

Multiple **Workers** execute those tasks in parallel. Finally, a **Synthesizer** combines their results into one answer.

## 2. How Does It Work?

```text
         User's Goal
              |
              v
       [ORCHESTRATOR]
        Lead AI Model
              |
              v
      Creates a Task Plan
       (Task 1 ... Task N)
              |
       +------+------+ 
       |      |      |
       v      v      v
    Worker  Worker  Worker
    Task 1  Task 2  Task N
       |      |      |
       +------+------+ 
              |
              v
       [SYNTHESIZER]
        Merges Results
              |
              v
        Final Answer
       + Any Known Gaps
```

**In simple words:**

1. The user provides a goal.
2. The Orchestrator understands the goal and creates a task plan.
3. Workers execute their assigned tasks simultaneously.
4. The Synthesizer combines the worker results into one answer.
5. If any worker fails or returns incomplete results, the final answer identifies the known gaps.

## 3. Example

**User's goal:** Research how to design a scalable payment system.

The Orchestrator might create these tasks:

| Worker | Responsibility |
|---|---|
| Worker 1 | Design the payment API. |
| Worker 2 | Research database and transaction handling. |
| Worker 3 | Design failure recovery and retries. |
| Worker 4 | Analyze security and fraud risks. |

All four workers run in parallel. The Synthesizer combines their findings into one payment-system design.

The number and nature of tasks are decided by the Orchestrator, not fixed in advance.

## 4. How Is This Different From Project 5?

| Aspect | Project 5: Parallelization | Project 6: Orchestrator-Workers |
|---|---|---|
| Task definition | Defined by the developer | Decided by the Orchestrator model |
| Number of tasks | Usually fixed | Can vary by goal |
| Execution | Multiple calls run in parallel | Planned tasks run in parallel |
| Final result | Reviews or votes are combined | Worker results are synthesized |
| Best suited for | Known, repeatable tasks | Complex goals with unknown subtasks |

**Rule of thumb:** If you already know the tasks, Project 5 is simpler and easier to control. If you don't know all the tasks in advance, Project 6 is more flexible.

## 5. Important Design Decisions

This project includes several safeguards and implementation choices:

- **Validate the plan:** Treat the model-generated plan as untrusted input and parse it carefully.
- **Limit the task count:** Prevent the Orchestrator from creating too many tasks.
- **Provide a fallback:** Use a one-task fallback if the generated plan cannot be parsed.
- **Isolate failures:** Allow other workers to finish even if one worker fails.
- **Limit context sharing:** Give each worker the titles of the other tasks rather than all their details.
- **Identify gaps:** Instruct the Synthesizer to report missing results rather than silently hiding failures.
- **Measure performance:** Track execution timing.
- **Support deployment and testing:** Provide a FastAPI service, automated tests, Docker packaging, and Terraform infrastructure.

These are implementation choices made for this project, rather than requirements of the general Orchestrator-Workers pattern.
