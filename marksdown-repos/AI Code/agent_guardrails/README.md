# Guardrails for agentic AI - runnable Python examples

Pure standard-library Python 3.9+, no installs, no API keys. The "model" is scripted so every run is
deterministic. The running example is a **Wealth Assistant** agent (holdings lookup, orders, emails).

    python 01_input_guardrails.py        # ...and so on, any order. Start with 11 for the big picture.

## The mental model: guardrails at every hop of the agent loop

    user -> [INPUT] -> agent loop ---------------------------------> [OUTPUT] -> user
                         |   think -> [TOOL] -> [DATA] -> [ACTION] -> [HUMAN] -> act -> observe
                         |   [LOOP] limits the whole cycle
                         +--- every hop writes [AUDIT];  [MONITOR] watches the fleet and can KILL it

| # | File | Question it answers | Example attack it stops |
|---|---|---|---|
| 01 | input | What may enter the model? | "Ignore previous instructions...", PII in prompts, booby-trapped documents (indirect injection) |
| 02 | tool | Which tools, with which arguments? | Unknown tools, wrong role, bad args, tool output carrying instructions |
| 03 | action | Should this side effect happen? | Over-limit orders, duplicate retries, after-hours trades, runaway loops draining an account |
| 04 | loop | Will it ever stop? | Infinite retries, circular searches, cost blow-ups, slow tools |
| 05 | output | What may leave? | Hallucinated numbers, leaked secrets, "guaranteed returns", invalid JSON |
| 06 | human | Who decides the risky ones? | Self-approval, junior approvals, silent timeouts, low-confidence actions |
| 07 | data | What may the agent know? | Cross-customer leaks, unmasked PAN, RAG documents the user cannot read |
| 08 | audit | Can we prove what happened? | Edited or deleted log entries, PII ending up in logs |
| 09 | monitoring | Is something going wrong right now? | Probing campaigns, traffic spikes, cost spikes -> automatic kill switch |
| 10 | extras (mine) | Four more defences | Data exfiltration (egress allow-list), `eval()` abuse, prompt leaks (canary), partial failures (undo stack) |
| 11 | pipeline (mine) | How do they fit together? | End-to-end run with eight requests and one audit chain |

## Principles worth remembering
1. **Enforce in code, not in the prompt.** "Please don't" is a request; an `if` statement is a guardrail.
2. **Defence in depth.** Regex filters get bypassed; the later layers (tool, data, action, human) still hold.
3. **Fail closed.** Unknown tool, missing approval, timeout, parse failure -> deny.
4. **Least privilege, using the end user's identity** for data access, not the agent's super-account.
5. **Make every layer observable** (audit + metrics), otherwise you cannot tune or trust it.

## Honest limits
These are teaching implementations. Production systems add trained classifiers (injection, toxicity, PII),
a proper policy engine (OPA / Cedar), an approval workflow tool, WORM audit storage, and real observability.
Frameworks that package some of this: NVIDIA NeMo Guardrails, Guardrails AI, LLM Guard, Llama Guard.
