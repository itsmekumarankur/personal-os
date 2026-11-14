# Project 12 — Streaming, Prompt Caching, Structured Outputs

> **Motto:** faster, cheaper, and in a shape your code can trust.

Three ideas that every production LLM feature ends up needing:

| Problem the business notices | Idea | One-line answer |
|---|---|---|
| "It feels slow." | **Streaming** | show words as they are written, so the *wait* shrinks |
| "The bill is huge." | **Prompt caching** | do not pay full price to re-read the same long prefix every time |
| "The next system choked on the output." | **Structured output** | force a shape, check types, check *meaning*, repair, or fail loudly |

Everything runs offline against a **fake model with a realistic event shape, latency shape and cache behaviour**. The point is to understand the mechanisms
(and see them break) before you spend money. `anthropic_live.py` shows the same ideas against the real API; I could not run it here.

```
pip install -r requirements-dev.txt
python experiments/exp1_streaming.py     # events, wire format, partial JSON, mid-stream errors
python experiments/exp2_caching.py       # what hits, what silently misses, TTL, parallel cold start, growing chats
python experiments/exp3_structured.py    # which validation layer catches which kind of wrong
python experiments/exp4_http.py          # real HTTP: TTFT, cancel on disconnect, resume, heartbeats
python bench.py                          # the "done when": TTFT, cost, hit rate with caching on/off
pytest -q                                # 26 tests (a safety net, not the point)
uvicorn server:app_factory --factory     # the SSE server
```

## Where each concept lives

| Concept | File | See it run |
|---|---|---|
| Stream events, rebuilding a message, partial tool JSON | `events.py` | exp1 |
| Reading half-typed JSON for a progress UI | `partial_json.py` | exp1 §3 |
| SSE wire format, parsing, keep-alives | `events.sse_line`, `sse_client.py` | exp1 §2, exp4 |
| Producer/consumer, cancel on disconnect, resume, heartbeat | `server.py` | exp4 |
| Prefix cache, breakpoints, TTL, lookback, minimums, concurrency | `cache_sim.py` | exp2 |
| Money: write 1.25x / read 0.1x, hit rate | `pricing.py` | exp2, bench |
| Forced-tool output, schema + semantic checks, repair loop | `structured.py` | exp3 |
| A model that streams, caches and misbehaves on purpose | `fake_model.py` | all |
| The real API version of all of the above | `anthropic_live.py` | (not run) |

---

## Part 1 — Streaming

### 1.1 Where the waiting comes from
```
 user clicks ──► network ──► queue ──► PREFILL ───────────► first token ──► DECODE: token, token, token ... ──► done
                                       (read the whole        ▲                  (about 20-60 ms each)
                                        prompt once)          └── TIME TO FIRST TOKEN (TTFT)
```
* **Prefill** is the model reading your whole prompt. Longer prompt = longer TTFT. This is why caching also improves TTFT (Part 2).
* **Decode** is writing the answer one token at a time. A 500-token answer at 40 tokens/s is 12 seconds, no matter what you do.
* **Streaming does not make the model faster.** It lets the user start reading at TTFT instead of at the end. Total time is identical (`exp1` §1).
  What changes is *perceived* latency, and the ability to **stop early** (cancel) and to **act on partial results** (show a tool call being prepared).

### 1.2 The event protocol (verified against the docs when written)
```
message_start            a Message with empty content; usage has input and cache numbers
 content_block_start     block #0 begins           {"type":"text"} or {"type":"tool_use","id","name","input":{}}
  content_block_delta ... text_delta | input_json_delta | thinking_delta | signature_delta   (many)
 content_block_stop      block #0 is complete
 content_block_start     block #1 ...
message_delta            stop_reason + CUMULATIVE usage.output_tokens
message_stop
ping  (anywhere)         error (anywhere, even mid-stream)
```
Rules a client must follow, each with a reason:
1. **Block `index` matters** — a reply can be `[text, tool_use, tool_use]`; deltas for different blocks carry their index.
2. **Tool input arrives as pieces of a JSON *string*** (`input_json_delta.partial_json`). Concatenate; parse **only after `content_block_stop`**.
   The `{}` in `content_block_start` is a placeholder (my first accumulator treated it as real input and a test caught it).
3. **`message_delta.usage` is cumulative** — replace, do not add.
4. **Unknown event types: ignore.** New ones appear over time.
5. **`error` can arrive after HTTP 200.** The status line is long gone, so errors are *in-band*. Keep the text you have; a half tool call is unusable.
   Recovery per the docs: capture the partial text and ask the model to continue from it (the exact mechanism differs by model generation, so read the current doc), or retry.

### 1.3 SSE on the wire
```
id: a1b2c3d4:7
event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"the answer "}}
                                                           <- blank line ends the event
: ping                                                     <- a comment: keep-alive, ignored by clients
```
Why SSE and not WebSockets: one-way server→client, plain HTTP (works through proxies/CDNs), built-in reconnect with `Last-Event-ID`. WebSockets are for two-way chatter.

### 1.4 The server design decisions (`server.py`) — each is a production incident somewhere
```
 browser ◄──SSE── CONSUMER (reads buffer, sends heartbeats, notices disconnect)
                      ▲ cursor
                  BUFFER  [open, message_start, delta, delta, ... done]
                      ▲ push
 model API ◄──── PRODUCER task (calls the model, fills the buffer)
```
* **Separate producer and consumer.** Then a dropped client does not have to kill the model call, and a reconnecting client can read the same buffer.
* **`on_disconnect="cancel"`** stops the producer when the last reader leaves: you stop paying for tokens nobody reads (`exp4` §2: 6 of ~300 events were ever generated).
  **`"keep"`** lets the call finish so the user can reconnect with `Last-Event-ID` and receive the remainder (`exp4` §3). It costs money if they never return.
  There is no right answer; it is a product decision. Mobile networks drop constantly, which argues for `keep` with a short timeout.
* **Heartbeat comments** (`: ping`) during silence (long prefill, long tool call). Load balancers and proxies drop connections that look idle.
* **Headers**: `Cache-Control: no-cache`, `X-Accel-Buffering: no` (nginx), and on AWS ALB raise the idle timeout above your longest silence. Buffering anywhere
  turns "stream" back into "wait, then everything", and you will only notice in production.
* **Resumable ids**: every event gets `streamid:n`; reconnect sends the last id, the server replays from n+1.

### 1.5 Streaming and structured data
`partial_json.py` reads `{"vendor": "Acme Tra` as `{"vendor": "Acme Tra"}` so a UI can fill a form while the model types. **It is a display hint only.**
`exp1` §3 shows it reading `561` while the real total is `561.48`. Act on the value only after `content_block_stop` and validation.

### 1.6 What to measure
TTFT (p50/p95), total time, tokens/second, stream error rate, cancel rate, "tokens generated but never read". Log `usage` from `message_start` and `message_delta`.

---

## Part 2 — Prompt caching

### 2.1 The idea
The model's expensive first step (prefill) turns your prompt into internal state. If tomorrow's request starts with **exactly the same tokens**, that state can be reused,
so you pay a fraction of the price for those tokens and skip most of the waiting. It is a **prefix** cache: it only helps for the *beginning* of the prompt.

```
 prompt is read in this order:      tools ─► system ─► messages (oldest ... newest)
                                    [=============== cached prefix ===============]|[ new part ]
                                                                  ▲ cache_control breakpoint
 usage:  cache_read_input_tokens  +  cache_creation_input_tokens  +  input_tokens(after the last breakpoint)  = total input
```

### 2.2 Rules (from the docs on the day I wrote this; re-check before relying — they change by model)
| Rule | Detail |
|---|---|
| Breakpoints | `cache_control: {"type":"ephemeral"}` on a block; **max 4** per request |
| Lifetime | **5 min** default, **refreshed for free on every hit**; `"ttl":"1h"` option |
| Price | write 5m **1.25x**, write 1h **2x**, read **0.1x** (some newer models list a lower read multiplier) |
| Minimum size | model-specific, **512 to 4096 tokens**; shorter prompts are **silently** not cached (both cache fields = 0) |
| Exact match | 100% identical prefix, up to and including the breakpoint block |
| Lookback | the system checks about **20 blocks** back from a breakpoint for an earlier entry |
| Concurrency | an entry is readable only **after the first response begins** |
| Invalidation | changing tools invalidates everything; system changes invalidate system+messages; `tool_choice`, images, thinking settings invalidate messages |

`cache_sim.py` implements these rules. It is a **simulator written from the docs**, not the service.

### 2.3 What you should see in the experiments (`exp2_caching.py`)
* **A.** 10 requests: cache off $0.116 vs on $0.037. The first request *costs more* (1.25x write); every later one costs a tenth for the prefix.
* **B. What breaks it.** Identical → hit. Different question *after* the breakpoint → hit. One character changed in the system prompt → **miss and re-write**.
  A timestamp at the **start** → miss every time. Tools in a different order → miss. **Rule: stable things first, volatile things last.**
  The classic bug is "Current time: 10:31:07" in the system prompt: a 0% hit rate that nobody notices because everything still works.
* **C. Time.** Hits refresh the clock; 350 s of silence expires it. If traffic is one request per 6 minutes, caching with 5-min TTL **loses money** (always pays 1.25x write).
  Options: a keep-alive request every <5 min, the 1-hour TTL (2x write), or no caching.
* **D. Parallel cold start.** 20 simultaneous requests on a cold cache = 20 writes. Send one, wait for its first token, then fan out.
* **E. Too short.** No error, no cache. **Always log both cache fields** and alert on hit rate.
* **G. Growing conversations.** Put the breakpoint on the newest block each turn; each turn reads the whole past and writes only the new part. If one turn adds
  more than ~20 blocks (tool-heavy loops), the old breakpoint is out of lookback range — add one in the middle.

### 2.4 Break-even arithmetic (do this before you enable it)
Let P = tokens in the fixed prefix, n = requests within one TTL window. Without cache: `n·P`. With: `1.25·P + (n−1)·0.1·P`. It wins from the **second** request in the window.
At n=1 it loses 25%. Hit rate = `cache_read / (read + creation + uncached)`; below ~50% something is invalidating it.

### 2.5 Layout checklist
1. Tools (stable, sorted deterministically) → 2. system (stable) → 3. large reference documents → 4. conversation history → 5. the new user turn.
Never put timestamps, user names, request ids or random ordering before the breakpoint. Changing `tool_choice` between calls invalidates the messages cache.

---

## Part 3 — Structured outputs

### 3.1 Why "please answer in JSON" is not enough
It works 95% of the time, which means 5% of your downstream jobs fail at 3 a.m. With a prompt-only approach you also get fenced code blocks, commentary,
trailing commas, and fields that are sometimes strings. So:

```
 LAYER 1 force the shape      one tool whose input_schema = your schema, tool_choice = that tool  (model MUST call it)
 LAYER 2 check the types      Pydantic: required fields, types, ranges, patterns, enums, dates               "schema" errors
 LAYER 3 check the MEANING    items add up to total · vendor really occurs in the source · date not in the future "semantic" errors
 REPAIR  send the exact errors back (is_error tool_result), at most N tries ──► then FAIL LOUDLY with every attempt
```
`exp3_structured.py` runs five model behaviours through three pipelines:

| model behaviour | schema only | + semantic | + repair ×3 |
|---|---|---|---|
| good | ok | ok | ok |
| sloppy (wrong types, missing field) | rejected | rejected | **fixed on attempt 2** |
| **hallucinating** (valid types, wrong values) | **ACCEPTED, WRONG** | rejected | **fixed on attempt 2** |
| stubborn (never improves) | rejected | rejected | rejected after 3 (no infinite loop) |

The lesson is the third row: **valid JSON is not correct JSON.** The wrong total and the invented vendor pass the schema. Only checks that compare the output with the
*source* or with *itself* catch them.

### 3.2 Schema design tips (these matter more than the repair loop)
* Give every field a description and a type as narrow as the truth: enums over free strings, `Decimal`/int cents over floats for money, ISO dates.
* Offer an escape hatch (`null` / `"unknown"`) for fields that may be absent — otherwise the model will invent a value to satisfy "required".
* Keep nesting shallow; ask for evidence (a quote from the source) when a field is easy to hallucinate, then **check the quote occurs in the source** (`structured.semantic_errors` does this for names).
* Schema lives in `tools`, the *first* thing in the cache order: changing it invalidates the whole cache. Version schemas deliberately.
* Some providers also offer native schema-constrained decoding. I did **not** verify the current availability for your model; check the docs. Even then keep layer 3: constraints guarantee *shape*, not *truth*.

### 3.3 The repair turn
The model sees its own previous call and a list of precise errors (`exp3`, last block). Rules: list *only* real errors, say which field, keep the attempts bounded,
count the extra tokens in the cost (the table in `/extract` shows total usage over attempts), and raise `ExtractionFailed` with all attempts so a human or a queue can handle it.

### 3.4 Where structure and streaming meet
A forced tool call streams as `input_json_delta` pieces. Use `partial_json` for the UI, wait for `content_block_stop` + layers 2-3 before acting.

---

## Part 4 — The three together
```
request ─► [tools: record_invoice schema] [system: rules + examples ◄── cache breakpoint] [user: the document]
              stable, cached                                              ▲ changes every call, uncached
response ─► stream ► input_json_delta ... ► content_block_stop ► validate ► (repair?) ► business system
```
* A big fixed instruction/example block + a tiny variable document is the ideal case for caching; structured extraction is exactly that shape.
* A repair turn re-sends the prefix: with caching it costs a read (0.1x), without it a full re-read. Caching makes repair cheap.
* Cancel on disconnect saves output tokens; caching saves input tokens. Track both.

## Architect's checklist
1. TTFT p95 and total time, per endpoint. 2. Cache hit rate and both cache fields logged on every call. 3. Timestamps/ids kept out of the prefix.
4. Idle timeout and buffering settings verified end-to-end (browser → CDN → LB → app). 5. Cancel/keep policy chosen on purpose.
6. Mid-stream error path tested. 7. Every structured output validated twice and bounded repair. 8. Semantic checks written with the domain owner.
9. A "give up" path that a human can see. 10. Prices and limits re-read from the docs, not from this README.

## Honest limits
* The model is **fake**. Latency numbers are invented (shape only). The cache is a **simulator** written from my reading of the docs; real behaviour may differ in detail
  (the exact rules for writes at several breakpoints and for lookback are simplified).
* Token counts are `chars/4`. Prices are placeholders.
* `anthropic_live.py` was written against the SDK's documented interface but **never executed** (no key, no network).
* SSE through a real proxy/CDN/ALB was not tested; only localhost.
* Resume works only while the buffer lives in server memory (one process, no TTL cleanup — a real service needs both).

## Exercises
1. Add `Retry-After`/rate-limit handling when the stream ends with `overloaded_error`: retry with backoff, continuing from the partial text.
2. Make the fake cache model *4 breakpoints* precisely (system, tools, doc, history) and write the layout that maximises hits for a RAG chat.
3. Add a keep-alive scheduler that pings the cache every 4 minutes only when the expected next request is within 10; compute when it pays for itself.
4. Add `evidence` quotes to the invoice schema and a check that each quote occurs in the source.
5. Replace the in-memory buffers with Redis streams; add a TTL and a max-buffer size.
6. Run `anthropic_live.py` with a real key; compare the real `usage` with `cache_sim` for the same prompts and list every difference.
