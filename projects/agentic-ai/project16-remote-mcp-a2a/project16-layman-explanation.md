# Project 16 — Remote Tools, OAuth and Agent-to-Agent in Very Simple Terms

Think of a **bank with several departments in different buildings**.

Earlier, the AI's tools were in the same room, so nobody asked for ID. Now the tools (and even other AI agents) sit in **other buildings**. Anyone could walk up. So every request needs a **visitor badge**.

The badge says: *who you are, which building it's valid for, what you may do there, whose account you're working on, and when it expires.*

---

## What Project 16 teaches

1. **Remote means four new questions.** Who are you? Which service is this for? What may you do? Whose data? Every request carries a signed badge (a token) that answers them.
2. **A badge is valid for ONE building.** A token made for the tools server must be refused by the agent server, even if the signature is genuine. This "audience" check is the most important one. Without it a service could pass your badge on to others and be tricked into misusing it.
3. **Services verify badges without phoning the issuer.** They check the signature using published public keys. If those keys can't be fetched, the service **refuses** (fail closed), it doesn't let people in.
4. **Short life.** Badges expire in minutes, so a stolen one soon dies.
5. **Acting on someone's behalf can only shrink power.** When agent A hands work to agent B, B gets a new, narrower badge: fewer permissions, shorter life, and a note of who is acting for whom. B can never receive more than A had.
6. **The system finds its own way.** A client that gets "401, unauthorized" is told where to read the rules and where to get a badge, so no one hard-codes addresses.
7. **A tool can quietly change after you approved it.** The project "pins" a tool's description, so if it changes later (a rug-pull) it is detected instead of trusted.
8. **Agent-to-agent work is a task with states.** Submitted, working, completed, failed or rejected, and only valid moves between states are allowed. Failures give a generic message to the caller, details stay in the logs.
9. **Leave a trail.** Each action is logged with the customer, the app and the acting agent, and a trace id follows the request across services.

---

## Why do we need it?

The moment tools and agents live on other machines or belong to other teams, "just trust it" stops working. For a bank-style system, this is the difference between a clever demo and something a security team would approve.

## The one-sentence takeaway

> Every hop needs proof of who is asking, for what, and for whom, and each hop can only pass on less power, never more.

**Honest limit:** everything ran for real over HTTP on one machine with fake bank data and no AI model. The Agent-to-Agent message shapes are a teaching subset, and the Docker setup was not run.
