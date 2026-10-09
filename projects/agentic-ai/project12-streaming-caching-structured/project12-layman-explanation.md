# Project 12 — Streaming, Caching and Structured Outputs in Very Simple Terms

Think of a **busy restaurant kitchen**.

**Streaming** is the waiter bringing each dish as it's ready, instead of making you wait until the whole 5-course meal is cooked. You start eating sooner, and if you don't like the starter you can cancel the rest.

**Caching** is the kitchen keeping the *prepared base sauce* ready. Every order starts with the same sauce. Preparing it fresh each time is slow and costs money. Reusing it is quick and cheap. But if the sauce goes cold (too much time passes) or you change its recipe, you must make it again.

**Structured outputs** is the order slip. If the cook writes the order in free handwriting, the billing counter can't read it. If it's a printed form with boxes (item, quantity, price), the counter can process it automatically. But a neat form can still contain a *wrong* price. Neat is not the same as correct.

---

## What Project 12 teaches

### Streaming
1. **The answer arrives in small pieces, not all at once.** Users see text immediately, so the app feels fast even if the total time is the same.
2. **Pieces of a tool call arrive as broken JSON.** You can only trust it after the "block finished" signal. Parsing half-finished data is only good for a progress hint.
3. **Failure can happen mid-stream, after the connection said "OK".** The error comes as an event inside the stream. Your code must watch for it.
4. **If the user closes the browser, decide what happens.** Cancel the work and stop paying, or keep going so they can resume later.
5. **Proxies can hold back your stream.** Without the right setting they buffer everything and streaming feels broken.

### Caching
6. **Only the unchanged beginning can be reused.** Order matters: tools, then instructions, then messages. Change one early word and everything after it becomes a miss.
7. **There is a minimum size and a time limit.** A prompt too small is silently not cached. An idle cache expires (about 5 minutes, refreshed each time it is used).
8. **First use costs a bit more, later use costs a lot less.** Writing the cache costs more than normal, reading it costs a fraction. It pays off only if you reuse it.
9. **Two requests arriving at the same moment both pay the write.** The cache isn't ready until the first one finishes.

### Structured outputs
10. **Three checks, not one.** (a) Make the model fill a form, (b) check the types are right, (c) check the values make sense, for example that the line items add up to the total.
11. **If it's wrong, ask again with the exact error, a limited number of times, then fail loudly.** Never loop forever and never quietly pass bad data on.

---

## Why do we need it?

Real products need to *feel* fast (streaming), be *affordable at scale* (caching), and produce data other systems can *trust* (structured outputs). Without these, a demo works but a bank-grade product doesn't.

## The one-sentence takeaway

> Send results early, don't pay twice for the same beginning, and never trust output just because it looks well-formed.

**Honest limit:** the model and the cache here are simulators written from the documentation. Token counts are rough and prices are placeholders. The live API file was not run.
