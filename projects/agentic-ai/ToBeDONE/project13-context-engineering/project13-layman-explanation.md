# Project 13 — Context Engineering in Very Simple Terms

Think of an **employee with a small desk**.

The AI can only "see" what is lying on its desk right now (the context). A long task produces paper: tool results, logs, old messages. The desk fills up. Then:
- it gets **slow and expensive**, because every step re-reads the whole pile, and
- the **important note gets buried**, or pushed off the desk completely.

**Context engineering** is the skill of *managing the desk*: deciding what stays, what's filed away, and what's thrown out.

---

## What Project 13 teaches

1. **Not everything on the desk is equally useful.** Old tool results (a huge log you already used) are the first thing to clear. Keep a *record that you called the tool*, drop the bulky answer.
2. **Throwing away the oldest stuff is dangerous.** Simple "keep the last N messages" lost a key instruction from early in the job. The old, important thing was the first to fall off.
3. **Summaries lose detail.** A casual summary dropped the exact value the task needed. A *structured* summary with a must-keep list (facts, user rules, decisions) kept it.
4. **Let the agent keep its own notes.** Writing key findings to a notebook outside the desk meant clearing the desk didn't lose them.
5. **Fetch just in time.** Don't pile 100 files on the desk. Keep a table of contents and pull the one needed page when needed.
6. **Use a helper with its own desk.** A sub-agent reads the 100 logs on *its* desk and returns a two-line answer. Your desk stays clean. (It protects your context, it doesn't make things cheaper by itself.)
7. **Cleaning the desk has a price.** Caching (Project 12) only works if the beginning stays unchanged. Clearing a little every turn keeps breaking the cache. Clearing in bigger batches, less often, is cheaper.
8. **Better "I can't find it" than a made-up answer.** When the needed fact was lost, the weak agent confidently invented one. The goal is an honest "not found".

---

## Why do we need it?

Long-running agents don't fail because the model is dumb. They fail because the **wrong stuff is on the desk**: too much, too old, or the key fact missing. For anything longer than a few steps, this decides quality *and* cost.

## The one-sentence takeaway

> Bigger memory is not the answer. The right things, in front of the model, at the right moment, is.

**Honest limit:** the model here is scripted (it only reacts to what's visible, which is the point). Token counts are rough. The live context-editing file was not run.
