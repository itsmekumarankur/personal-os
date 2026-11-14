"""LG-01  The smallest possible graph: State + Node + Edges.  No LLM, no API key.  Run: python lg_01_hello_graph.py"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):          # 1) STATE: the shared notebook every node can read/write
    name: str
    greeting: str


def greet(state: State) -> dict:     # 2) NODE: a plain function. Takes state, returns ONLY what it changes.
    return {"greeting": f"Hello, {state['name']}!"}


builder = StateGraph(State)
builder.add_node("greet", greet)
builder.add_edge(START, "greet")      # 3) EDGES: the arrows. START and END are built-in markers.
builder.add_edge("greet", END)
graph = builder.compile()             # 4) COMPILE: validates the graph and gives you a runnable app

result = graph.invoke({"name": "Ankur"})
print(result)                         # {'name': 'Ankur', 'greeting': 'Hello, Ankur!'}  <- final state


"""
        INPUT STATE
     {"name": "Ankur"}
              |
              v
     +------------------+
     |   greet NODE     |
     |                  |
     | Reads: name      |
     | Creates greeting |
     +------------------+
              |
              v
        UPDATED STATE
  {"name": "Ankur",
   "greeting": "Hello, Ankur!"}
              |
              v
             END

Concept. A graph has shared STATE, NODES (functions) that update it, and EDGES (arrows) that say what runs next.

Architecture view. State is the shared notebook. Nodes never call each other; they only read and write state.
"""