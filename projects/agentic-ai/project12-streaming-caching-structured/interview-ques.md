# Chapter 12: Streaming, Caching, and Structured Outputs
## Agentic AI Concepts for AI Architect Interviews

This version focuses on transferable concepts an interviewer can assess across Agentic AI systems, rather than questions tied to a particular lab, code sample, provider event, or project.

This chapter explains three important ideas for building AI applications:

1. **Streaming** — show the answer while AI is generating it.
2. **Caching** — reuse work that has already been done to reduce cost.
3. **Structured outputs** — make AI return data in a predictable format, then check that the data is correct.

---

**# Round 1 — Explain the Basics Simply**

**## Q1. If streaming does not make AI generate faster, why use it?**

Streaming means showing the answer little by little while AI is still working. It is like watching someone type a message instead of waiting for them to finish typing everything. The total time AI takes may stay the same, but the user can start reading sooner.

**Remember:** Streaming helps users see answers sooner. It can also save money if the user stops the answer early. But it does not automatically make AI do less work.

**---**

**## Q2. What happens when AI streams an answer that includes a tool call?**

Sometimes AI needs help from another tool, like a calculator, to answer a question. AI sends a request to the tool, the system collects the complete request, and then the tool does the work. The result comes back to AI, which uses it to give the final answer.

**Remember:** The tool request may arrive in small pieces. The system must collect all the pieces before using the tool, just as you must collect all the parts of a message before understanding it correctly.

**---**

**# Round 2 — Real-World Design Problems**

**## Q3. What if AI fails after the server has already started streaming the answer?**

**Simple explanation:** Imagine AI starts answering and then suddenly stops because of an error. The user has already seen part of the answer, so the system cannot pretend the answer is complete. It should tell the user that something went wrong and offer another attempt when appropriate.

**Remember:** Never treat a half-finished answer as a complete answer. If AI has already performed an action, such as making a payment, check that retrying will not perform the same action twice.

**---**

**## Q4. What if the user closes the browser while AI is generating a long answer?**

**Simple explanation:** The system has two choices. It can stop AI to avoid wasting money, or it can let AI continue and save the answer so the user can see it later. The best choice depends on whether the answer is worth finishing even after the user leaves.

**Remember:** Stop ordinary chat generation when continuing has little value. For important, lengthy work, continuing and allowing the user to return may be more useful.

**---**

**## Q5. Streaming works on my laptop but arrives as one big response in production. What should I check?**

**Simple explanation:** AI may be sending words one by one, but another part of the system may be collecting all the words before showing them to the user. It is like water flowing through a pipe but getting held up in a container before coming out.

```text
AI sends small pieces
        |
        v
Network or server collects them
        |
        v
All pieces are sent together
        |
        v
User sees the answer at once
```

Check whether a proxy, network component, or server is holding the response instead of forwarding each piece immediately. Test the complete production route, not just your laptop.

**Remember:** Find where the pieces are getting held up. Simply increasing the waiting time may not solve the problem.

**---**

**## Q6. The prompt contains 6,000 tokens, and many users ask short questions. How can caching reduce cost?**

**Simple explanation:** Imagine a teacher gives the same instructions to every student. Instead of preparing those instructions from scratch every time, the system can reuse the common part. In AI, caching can save time and money by reusing repeated instructions instead of processing them from scratch for every request.

**### Without prompt caching**

```text
Request 1: Common instructions + Question 1
Request 2: Common instructions + Question 2
Request 3: Common instructions + Question 3

AI repeatedly processes the common instructions.
```

**Remember:** Keep common instructions unchanged and put changing information, such as the user's question, later. Caching works only when the system can reuse the same content according to the provider's rules.

**---**

**## Q7. Cache hit rate was 90% last week but only 5% today. What could have changed?**

**Simple explanation:** A cache hit means the system found information it had already saved and could reuse it. If the hit rate suddenly falls, something may have changed, so the system can no longer reuse that information as often. For example, someone may have changed the instructions, added a timestamp, or allowed the saved information to expire.

Compare the old and new prompts, check whether the cache has expired, and look at the cache usage reports to find the cause.

**Remember:** A sudden drop in cache hits can increase AI costs. Find out what changed before trying to fix it.

**---**

**# Round 3 — Structured Outputs**

**## Q8. “We use JSON mode, so the AI output is always correct.” Is that true?**

**Simple explanation:** No. JSON is just a way of arranging information in a fixed format. AI can follow the format perfectly and still give wrong information. For example, an invoice may contain all the required fields but have the wrong total.

**Remember:** Check three things: whether the information is arranged correctly, whether the values are of the right type, and whether the information makes sense. Correct formatting does not guarantee correct answers.

**---**

**## Q9. How should an AI output-repair loop work?**

**Simple explanation:** Sometimes AI makes a mistake in the data it returns. The system can show AI what went wrong and ask it to try again. But it should limit the number of attempts. If AI keeps making the same mistake, the system should stop and report the problem instead of trying forever.

**Remember:** Give AI clear error messages, allow only a few retries, and ask a person to review the result if AI still cannot fix it. Never treat incorrect data as a successful result.
---

**# Round 4 — Security and Monitoring**

**## Q10. What if a user asks AI to reveal its system prompt while it is streaming?**

A system prompt is like a secret instruction sheet that tells AI how to behave. If a user asks AI to reveal these instructions, the system should protect them. Once AI sends secret information to the user, it cannot take it back. So, it is better to protect secrets before AI starts answering.

**Remember:** Never put passwords or important secrets where AI could reveal them. Give AI access only to the information and tools it really needs.

**---**

**## Q11. How do you show token usage and cost per request on a dashboard?**

**Simple explanation:** Every time AI works, it uses tokens, which are small pieces of text. Using tokens costs money. A dashboard is like a report card that shows how many tokens AI used, how much each request cost, and how long it took to answer. It can also show how many tokens were saved by reusing cached information.

**Remember:** Count token usage correctly. If the same total is counted more than once, the dashboard will show a higher cost than the real cost.

**---**

**## Q12. Should we cache everything, including user-specific data?**

**Simple explanation:** Caching means saving information so it can be reused instead of doing the same work again. For example, AI can reuse common instructions for many users. But one user's private information must never accidentally be shown to another user. This is especially important in a bank, where customer information must stay private.

**Remember:** Reuse common information to save time and money, but protect each user's private data. Always make sure the caching system keeps customer information separate.


## Final Summary: Remember These Three Ideas

```text
STREAMING
Show the answer as it arrives.
Focus: user experience, partial failures, network buffering.

CACHING
Reuse stable content instead of processing it from scratch.
Focus: identical prefixes, cache hit rate, cost, privacy.

STRUCTURED OUTPUTS
Make AI return data in a predictable format and verify it.
Focus: schema, types, business meaning, bounded retries.
```
