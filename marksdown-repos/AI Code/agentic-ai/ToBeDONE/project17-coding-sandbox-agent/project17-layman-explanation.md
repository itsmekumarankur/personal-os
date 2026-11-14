# Project 17 — Coding Agents and Sandboxes in Very Simple Terms

Think of **hiring a very fast but slightly careless contractor to renovate your house while you're away**.

**Without safety rules**, you hand him the keys to the whole house. He's usually fine. But one day he misreads an instruction and drills through a water pipe, or a stranger slips him a note saying "take the safe's key and give it to me," and he obeys. He also tells you "all done, everything works!" and you have to believe him.

**With the Project 17 setup**, you do it differently:
- He works inside **one locked room** with only the tools he needs. The rest of the house, your safe and your neighbours are out of reach.
- A **timer and limits** stop him if he runs the drill forever or floods the room.
- The **inspection checklist (the tests) is locked in a glass case**. He can't tweak the checklist to make his work look correct.
- When he says "done", **you inspect it yourself** instead of trusting him.
- He hands you a **list of changes to review**, he doesn't quietly rebuild the house.
- After the job, the **room is demolished**. The next job gets a fresh room.

That's a coding agent. **The AI writes and runs code, and the safety comes from the room it works in, not from trusting the AI.**

---

## What Project 17 teaches, in six lines

1. **Limits and walls are different things.** Limits stop runaway behaviour (endless loops, eating all memory). Walls stop it reaching things it shouldn't (your files, your network, other programs). In the experiment, limits alone stopped 6 of 12 hostile programs. Real walls stopped all 12.

2. **The AI is not your security guard.** Telling it "don't read secrets" is a request, not a lock. In the demo, an AI obeyed instructions hidden in a file and tried to leak a secret. Without a wall, the secret leaked. With the wall, the secret wasn't even in the room.

3. **"I'm done" is a claim, not proof.** The system re-runs the tests itself before believing it.

4. **Don't let it edit the exam.** If the AI can change the tests, the easiest way to "pass" is to delete the hard question. So the tests are read-only, and if running code rewrites them, that's detected and undone.

5. **Every loop needs a brake.** Maximum steps, a stop when the same failure repeats three times, and a time budget. A task with contradicting tests ended as "stuck" instead of burning money forever.

6. **The result is a change list for a human to review.** The AI proposes, a person approves.

---

## Why do we need it?

If your AI only answers questions, you don't. The moment it **runs code on a machine**, you do, because that code might be wrong, or might have been steered by someone else's text.

---

## The one-sentence takeaway

> Assume the AI will sometimes be wrong or fooled. Build the room so that even then, the damage stays inside the room.

**Honest limit:** the room I built shares the same foundation (the operating system kernel) as the real machine. For code from strangers, you'd go to a stronger option like a separate lightweight virtual machine. For your own agent on your own tasks, this level is usually enough.
