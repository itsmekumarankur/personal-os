"""LG-11  Parallel nodes (fan-out / fan-in) + two data sources.  Run: python lg_11_parallel_fanout.py"""
import operator, sqlite3
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from common import get_llm, ensure_demo_db

DB = ensure_demo_db()
POLICY_NOTES = {                                  # stand-in for a vector store / document DB (see LC-14 for the real thing)
    "return": "Items can be returned within 7 days if unopened.",
    "warranty": "Keyboards and monitors carry a 1-year warranty.",
}


class State(TypedDict):
    question: str
    context: Annotated[list[str], operator.add]    # reducer lets BOTH parallel nodes append safely
    answer: str


def sql_lookup(s: State):
    print("  [sql_lookup]    running on SQLite")
    rows = sqlite3.connect(DB).execute("SELECT name, price, stock FROM products").fetchall()
    return {"context": [f"DB product: {n}, price Rs.{p}, stock {st}" for n, p, st in rows]}


def policy_lookup(s: State):
    print("  [policy_lookup] running on policy notes")
    hits = [text for key, text in POLICY_NOTES.items() if key in s["question"].lower()]
    return {"context": [f"POLICY: {h}" for h in hits]}


def answer(s: State):
    print("  [answer]        both lookups finished, now the LLM")
    prompt = "Answer using ONLY this context.\n" + "\n".join(s["context"]) + f"\n\nQuestion: {s['question']}"
    return {"answer": get_llm().invoke(prompt).text}


b = StateGraph(State)
b.add_node("sql_lookup", sql_lookup)
b.add_node("policy_lookup", policy_lookup)
b.add_node("answer", answer)
b.add_edge(START, "sql_lookup")                    # two edges out of START = fan-out (run in the same step)
b.add_edge(START, "policy_lookup")
b.add_edge(["sql_lookup", "policy_lookup"], "answer")    # list = WAIT for both = fan-in
graph = b.compile()

out = graph.invoke({"question": "Is the Webcam in stock, and what is the return policy?", "context": []})
print("\ncontext collected:", len(out["context"]), "items")
print("ANSWER:", out["answer"])


"""
       USER QUESTION
 "Is Webcam in stock, and what
       is the return policy?"
                |
          +-----+-----+
          |           |
          v           v
 +----------------+  +------------------+
 |  SQL LOOKUP    |  |  POLICY LOOKUP    |
 | Searches shop  |  | Searches policy   |
 | database       |  | notes              |
 +----------------+  +------------------+
          |           |
          v           v
    Product data    Return policy
    Price, stock    Relevant rules
          |           |
          +-----+-----+
                |
                v
       +------------------+
       |   COMBINE DATA   |
       | Wait for BOTH    |
       | lookups to finish|
       +------------------+
                |
                v
       +------------------+
       |   ANSWER NODE    |
       | Sends combined   |
       | context to LLM   |
       +------------------+
                |
                v
          FINAL ANSWER
          
"""