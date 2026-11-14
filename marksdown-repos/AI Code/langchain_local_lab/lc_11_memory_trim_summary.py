"""LC-11  Memory grows forever - two ways to control it: TRIM and SUMMARIZE.  Run: python lc_11_memory_trim_summary.py"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, trim_messages
from common import get_llm

history = [
    SystemMessage("You are a concise assistant."),
    HumanMessage("Hi, I'm Ankur."),            AIMessage("Hello Ankur!"),
    HumanMessage("I work in fintech."),        AIMessage("Nice, fintech is broad."),
    HumanMessage("I manage 80 microservices."), AIMessage("That's a big estate."),
    HumanMessage("What did I say I manage?"),
]

# ---- Option 1: TRIM - keep only the last N messages (runs without any LLM) ----
trimmed = trim_messages(
    history,
    max_tokens=4,            # with token_counter=len this means "4 messages"
    token_counter=len,       # swap for the model itself to count real tokens
    strategy="last",
    include_system=True,     # always keep the system prompt
    start_on="human",
)
print("TRIM keeps", len(trimmed), "of", len(history), "messages:")
for m in trimmed:
    print(f"  [{m.type}] {m.content}")

# ---- Option 2: SUMMARIZE - compress the old part into one message (uses the LLM) ----
llm = get_llm()
old, recent = history[1:-1], history[-1:]
transcript = "\n".join(f"{m.type}: {m.content}" for m in old)
summary = llm.invoke(f"Summarize this conversation in 2 short sentences, keep all facts:\n{transcript}").text
compact = [history[0], SystemMessage(f"Summary of earlier conversation: {summary}")] + recent
print("\nSUMMARY memory ->", summary)
print("answer using summary:", llm.invoke(compact).text)


"""
Concept:
 History grows without limit and costs tokens. 
 Two standard fixes: drop old messages, or compress them.

New things in this step

trim_messages with strategy='last' and include_system=True
A summary message that replaces many old messages
The trade-off: trimming forgets, summarising approximates
Architecture view:
-  Both happen BEFORE the model call, on the list you are about to send.
   The stored history can stay complete.
"""