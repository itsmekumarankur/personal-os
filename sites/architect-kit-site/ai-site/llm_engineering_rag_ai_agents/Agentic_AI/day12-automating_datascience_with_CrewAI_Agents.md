# 🤖 Automating Data Science with CrewAI Agents — The Journey Map

> A friendly, step-by-step walkthrough of what this notebook actually *does*, from "empty notebook" to "a team of AI agents that plans, codes, and runs an entire machine learning workflow by itself." Read it like a story — each stop builds on the last.

---

## 🗺️ The Big Picture

Think of this notebook as **seven stops on a road trip**:

```
🏁 START      📊 THE MANUAL WAY (RECAP)      🧩 CREWAI 101      🔧 SETUP + CODE EXECUTOR TOOL
Overview  →  Remember Day 12's ML Notebook →  Agents/Tasks/Crews  →  Let Agents Run Real Code

🧑‍🔬 DEFINE THE AGENTS      📋 DEFINE THE TASKS      🚀 RUN THE CREW
Planner + Analyst + Modeler  →  What Each Agent Must Do  →  Watch AI Do the Whole ML Project
```

By the end, you go from "I manually wrote every line of a machine learning pipeline" (Day 12's notebook) to "a team of three AI agents plans, writes, and executes that *entire* pipeline themselves, with me just pressing go."

---

## Stop 1 — 🏁 Project Overview: Automating Data Science with CrewAI Agents
**What's happening:** Screenshots preview the ambitious goal — instead of a human writing every step of a data science project, a **crew of AI agents** will do it: inspecting data, preprocessing it, training a model, and evaluating results, entirely on their own.

**Why it matters:** This sets up the central question of the whole notebook: can AI agents genuinely replace the manual, step-by-step data science workflow you did by hand elsewhere?

---

## Stop 2 — 📊 Build, Train & Evaluate ML Regression Models (Manually) — Recap
**What's happening:** A quick pointer back to the companion notebook (`Predictive Analytics Using Machine Learning.ipynb`) that walked through the *manual* version of this same workflow — EDA, cleaning, missing values, Linear Regression, Random Forest, XGBoost, evaluation. Experienced folks are told they can skip straight ahead.

**Why it matters:** This is the deliberate "before" picture — everything the AI crew is about to automate was, in that earlier notebook, done by hand, line by line.

---

## Stop 3 — 🧩 Understand CrewAI Components
**What's happening:** A conceptual introduction to **CrewAI**, a framework for orchestrating multiple LLM-powered agents working together. The core building blocks:
- **Agents** — individual AI workers, each defined by a `role` (job title), `goal` (objective), `backstory` (persona/context), an `llm` (the model powering their reasoning), optional `tools`, and whether they can delegate work to others
- **Tasks** — specific assignments given to agents
- **Crew** — the overall team, running tasks in a defined process (e.g., sequentially)

**Why it matters:** This is the vocabulary for everything that follows — every later stop is just filling in these building blocks with real specifics for a data science project.

---

## Stop 4 — 🔧 Loading Key Libraries & the `NotebookCodeExecutor` Tool
**What's happening:**
- Installs `crewai` and imports `Agent`, `Task`, `Crew`, `Process`
- Loads the OpenAI API key from `.env` and sets up the LLM (`gpt-4.1-mini`) that will power the agents' reasoning
- The real star of this stop: a custom **`NotebookCodeExecutor`** tool. This tool lets an agent write Python code as text, and then actually **execute it live inside the notebook's own environment** using `exec()` — meaning agent-written code can read and modify real variables like `shared_df`
- The sample sales CSV is loaded into `shared_df`, a global DataFrame the agents' generated code will operate on

> ⚠️ **Heads-up:** The notebook itself flags this clearly — running arbitrary AI-generated code with `exec(code, globals())` carries real security risk. This is appropriate for a controlled learning sandbox, but isn't something to point at untrusted inputs or production systems without serious safeguards.

**Why it matters:** Without this tool, agents could only *talk about* doing data science — this tool is what lets them actually *do* it, by writing and running real Python against real data.

**Practice challenge:** Write a new function that joins two strings with an underscore, and use the tool to execute it — a simple sanity check that the executor works before trusting it with a full ML pipeline.

---

## Stop 5 — 🧑‍🔬 Defining the Agents with Code Generation Focus
**What's happening:** Three specialized agents get created, each aimed at *writing and executing* code via the `NotebookCodeExecutor` tool:
- **Planner Agent** — the "Lead Data Scientist," who doesn't touch code directly but lays out the step-by-step plan (inspect → preprocess → model → evaluate) and instructs the other agents on the *goals* for each step
- **Analyst/Preprocessor Agent** — writes and runs the code for data inspection, cleaning, and preprocessing (handling dates, dropping identifiers, one-hot encoding, and building the train/test split)
- **Modeler/Evaluator Agent** — writes and runs the code that trains a model and evaluates its performance

**Why it matters:** This mirrors a real data science team's division of labor — a planner sets direction, while specialists execute — except every "specialist" here is an LLM that writes its own code on demand.

---

## Stop 6 — 📋 Defining Key Tasks & Responsible Agent
**What's happening:** Each agent gets a concrete `Task` with detailed, high-level instructions — not literal code, but clear objectives the agent must translate into code itself:
- **Planning Task** — outlines the full pipeline sequence and reminds each agent to use the `NotebookCodeExecutor` tool to write and run real code
- **Data Analysis & Preprocessing Task** — instructs: inspect `shared_df`, convert and sort by `Date`, drop identifier columns, one-hot encode `Platform`, and create global `X_train`/`X_test`/`y_train`/`y_test` variables
- **Modeling & Evaluation Task** — instructs: train a `RandomForestRegressor` (`random_state=42`) on the global training variables, store it as `trained_model`, predict on the test set, and report evaluation metrics

**Why it matters:** This is the "job description" stop — tasks translate the Stop 5 agents' general roles into precise, checkable objectives for this specific dataset and prediction goal.

---

## Stop 7 — 🚀 Creating and Running the Crew
**What's happening:** The three agents and three tasks are assembled into a `Crew`, configured with `Process.sequential` (each task runs in order, building on the previous one's work) and `verbose=1` so you can watch the agents' reasoning and tool calls unfold live. Calling `.kickoff()` sets the whole pipeline running autonomously — the Planner lays out the plan, the Analyst inspects and preprocesses the real data, and the Modeler trains and evaluates a Random Forest model, all through agent-generated, agent-executed Python code. The final result (`crew_result.raw`) is displayed as the finished report.

**Why it matters:** This is the payoff moment — the entire manual workflow from the companion notebook (Stop 2) now runs end-to-end, autonomously, with three AI agents collaborating instead of a human writing each line.

**Practice challenge:** Add a Decision Tree Regressor into the comparison, and modify the Analyst agent's instructions so the train/test split uses shuffling — a good test of how precisely you can steer agent-generated code just by editing its written goal description.

---

## 🏆 What You Walk Away With
By the end of this notebook, you've built a genuinely autonomous **AI-driven data science pipeline**:

✅ Learned CrewAI's core building blocks — Agents, Tasks, and Crews
✅ Built a custom tool (`NotebookCodeExecutor`) letting agents write *and run* real Python code
✅ Defined a Planner, an Analyst/Preprocessor, and a Modeler/Evaluator — each with a distinct role
✅ Wrote detailed task instructions that guide agents toward specific, checkable data science objectives
✅ Assembled and ran a sequential Crew that completed an entire ML workflow autonomously
✅ Practiced steering agent behavior purely by editing role/goal/task text, without touching the underlying pipeline code yourself

**Next natural steps** (not in this notebook, but the logical continuation): adding a fourth agent to handle visualization/reporting, or swapping `Process.sequential` for `Process.hierarchical` to let a manager agent dynamically delegate work instead of following a fixed order.

---

*Guide generated from `day12-automating_datascience_with_CrewAI_Agents.ipynb`*
