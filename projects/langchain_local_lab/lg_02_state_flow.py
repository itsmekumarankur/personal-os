"""LG-02  Watch state flow through several nodes.  No LLM.  Run: python lg_02_state_flow.py"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    text: str
    cleaned: str
    word_count: int
    shout: str


def clean(s: State):  return {"cleaned": " ".join(s["text"].split())}
def count(s: State):  return {"word_count": len(s["cleaned"].split())}
def shout(s: State):  return {"shout": s["cleaned"].upper() + "!"}


b = StateGraph(State)
for name, fn in [("clean", clean), ("count", count), ("shout", shout)]:
    b.add_node(name, fn)
b.add_edge(START, "clean"); b.add_edge("clean", "count"); b.add_edge("count", "shout"); b.add_edge("shout", END)
graph = b.compile()

inp = {"text": "  langgraph   makes   state   explicit  "}

print("--- stream_mode='updates': only what EACH node changed ---")
for update in graph.stream(inp, stream_mode="updates"):
    print(update)

print("\n--- stream_mode='values': the FULL state after each step ---")
for full_state in graph.stream(inp, stream_mode="values"):
    print(full_state)


"""
        INPUT STATE
  "  langgraph   makes   state   explicit  "
                    |
                    v
          +------------------+
          |   clean NODE     |
          | Remove extra     |
          | spaces           |
          +------------------+
                    |
                    v
          cleaned = "langgraph makes state explicit"
                    |
                    v
          +------------------+
          |   count NODE     |
          | Count the words  |
          +------------------+
                    |
                    v
          word_count = 4
                    |
                    v
          +------------------+
          |   shout NODE     |
          | Convert to       |
          | uppercase + !    |
          +------------------+
                    |
                    v
          shout = "LANGGRAPH MAKES STATE EXPLICIT!"
                    |
                    v
                   END


Concept. stream() lets you see each step. 'updates' shows what each node changed; 'values' shows the whole state each time.

New things in this step

stream_mode='updates' vs 'values'
Three nodes in a chain
State accumulates; untouched keys stay
Architecture view. Each node's return value is merged into the state, then the next node runs on the merged state.
"""