# Architect Interview — Chapter 13: Context Engineering
## Simple Notes for Agentic AI Architect Interviews

This chapter explains how to help an AI agent remember the important information, avoid carrying too much unnecessary information, and work reliably on long tasks.

---

# Round 1 — Explain the Basics Simply

## Q1. Why can an AI agent become worse during a long task, even when it has a large context window?

**Simple explanation:** An AI agent uses its conversation and other information as its working memory. During a long task, too much old information can make it harder to focus on what matters. Processing all that information again and again can also increase cost and response time. A bigger memory helps, but it does not solve the problem of keeping the right information.

**Remember:** Do not just give an agent more memory. Help it keep the important information and remove unnecessary details.

**---**

## Q2. What information should an agent keep, and what can it safely remove?

**Simple explanation:** An agent should keep the goal, the user's important instructions, decisions already made, and facts needed to finish the task. It can often remove old details that are no longer useful, such as lengthy results from tools it has already used. Before removing anything, the system should make sure that the information will not be needed later.

**Remember:** Keep the facts and rules that guide the task. Remove information only when you are confident it is no longer needed.

**---**

# Round 2 — Choosing the Right Strategy

## Q3. What are the different ways to manage an agent's memory during a long task?

**Simple explanation:** There are several ways to stop an agent's working memory from becoming too large. A sliding window keeps only the newest part of the conversation, but it might accidentally remove an important early instruction. A summary saves the main ideas in fewer words, but it might leave out an exact detail. Clearing old tool results saves space, but the agent may need to fetch those results again. A structured note can preserve important facts, decisions, and unanswered questions. In practice, combining these methods is often more reliable than depending on just one.

**Remember:** No single method is perfect. Choose a combination that saves space without losing important facts.

**---**

## Q4. What is a “must-keep” list, and why does an agent need one?

**Simple explanation:** A must-keep list is a small note containing information the agent must not forget while working. For a loan investigation, it might include the loan ID, confirmed facts, the user's restrictions, decisions already made, and questions that still need answers. The system should keep this list separate from ordinary conversation history so that routine cleanup does not remove it. Important facts should also say where they came from, so they can be checked again if needed.

**Remember:** Keep important facts in a protected, easy-to-find place, and record where those facts came from.

**---**

## Q5. Should an agent load all available documents and logs at once, or fetch information only when needed?

**Simple explanation:** If an agent has 100 log files, loading all of them at once can fill its memory with information it may never use. A better approach is to keep a list describing what each file contains and fetch the relevant file or lines only when needed. This is like using a book's index to find the right page instead of reading the whole book every time. The downside is that the agent must search well and may need extra tool calls.

**Remember:** Retrieve information when it is needed instead of filling the agent's memory with everything available.

**---**

## Q6. When should an agent use a sub-agent for a large investigation?

**Simple explanation:** A sub-agent is like asking a helper to investigate one part of a large problem. The helper can read many documents using its own working memory and return a short report. This keeps the main agent's memory from becoming overloaded. However, sub-agents do not automatically make the work cheaper. They can miss important details or make mistakes, so the main agent should check their findings and ask for sources when accuracy matters.

**Remember:** Sub-agents can protect the main agent from too much information, but their results still need checking.

**---**

# Round 3 — Reliability and Failure Modes

## Q7. How can context management affect prompt caching?

**Simple explanation:** Prompt caching can save work when the beginning of repeated requests stays the same. If the system frequently changes or removes parts of that beginning, the cache may not be reusable and costs can rise. Clearing old information in large, planned batches can sometimes preserve more of the repeated content than constantly changing it. The best approach depends on the agent's workload, so measure both the savings from clearing information and the effect on caching.

**Remember:** Context cleanup can save tokens, but frequent changes can reduce caching benefits. Measure the total cost rather than looking at token count alone.

**---**

## Q8. What if the agent forgets a fact and confidently gives the wrong answer?

**Simple explanation:** When the information it needs is missing, an AI may guess and sound confident even when it is wrong. The system should teach the agent that saying “I could not find the evidence” is better than making something up. For important claims, the agent should show where the information came from, and another step should check whether the source really supports the answer.

**Remember:** A confident answer is not always a correct answer. Require evidence for important claims and allow the agent to say when it does not know.

**---**

## Q9. What should you do if the agent forgets an important user instruction during a long conversation?

**Simple explanation:** First, check what information the agent actually received when it made the mistake. The instruction might have been removed while old messages were being cleared, or it might still have been present but overlooked. Keep important instructions in a dedicated place that stays visible, reduce unnecessary information, and add a test to make sure the same mistake does not happen again.

**Remember:** Find out whether the instruction was lost or simply ignored. Keep critical rules easy to find and test that they remain available during long tasks.

**---**

# Round 4 — Security and Long-Running Tasks

## Q10. What if a tool returns malicious instructions inside a document or log?

**Simple explanation:** A document or log may contain text that tells the AI to ignore its rules or reveal private information. The agent must treat that text as information to examine, not as a new instruction to obey. Summarising the text can be risky too, because a summary might accidentally make the malicious instruction look like a trusted rule. Keep track of where information came from and verify it before treating it as trustworthy.

**Remember:** Text found in a document is not automatically a trusted instruction. Keep the source attached to important facts and do not turn untrusted text into trusted notes.

**---**

## Q11. How can an agent continue a task after a restart or the next day?

**Simple explanation:** The agent's current conversation memory may disappear when the process stops. For a task that lasts hours or days, save the important progress somewhere durable, such as a database or task record. Save what has been completed, important decisions, current status, and what needs to happen next. When the agent starts again, it can read those notes and fetch any evidence it needs again.

**Remember:** Do not rely on conversation memory alone for long-running work. Save important task state outside the conversation so it can survive restarts.

**---**

# Final Summary — Remember These Ideas

```text
MANAGE CONTEXT
Keep important instructions and facts.
Remove details that are no longer needed.

RETRIEVE WHEN NEEDED
Search for relevant information instead of loading everything.

USE NOTES AND SUB-AGENTS
Save important progress and delegate large investigations carefully.

VERIFY ANSWERS
Use evidence, track where facts came from, and allow "I don't know."

PROTECT AND SAVE STATE
Treat retrieved text as untrusted and save progress for long-running tasks.
```

**Interview tip:** Explain the problem in plain language, describe the design you would choose, and mention the trade-off or risk. That shows you understand the concept rather than just memorising terms.
