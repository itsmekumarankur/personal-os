"""LG-05  Cycles: loop until a condition is met (the heart of agents).  No LLM.  Run: python lg_05_loops.py"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    draft: str
    attempts: int


def improve(state: State):
    n = state["attempts"] + 1
    new = state["draft"] + f" +detail{n}"        # pretend an LLM made the draft better
    print(f"  [improve] attempt {n}: {new!r}")
    return {"draft": new, "attempts": n}


def good_enough(state: State) -> str:
    if len(state["draft"]) >= 30 or state["attempts"] >= 5:   # ALWAYS keep a max-attempt guard
        return "done"
    return "again"


b = StateGraph(State)
b.add_node("improve", improve)
b.add_edge(START, "improve")
b.add_conditional_edges("improve", good_enough, {"again": "improve", "done": END})   # <- edge pointing BACK = a loop
graph = b.compile()

print(graph.invoke({"draft": "start", "attempts": 0}))

# Safety net: LangGraph itself stops runaway loops (default recursion_limit = 25).
try:
    runaway = StateGraph(State)
    runaway.add_node("improve", improve)
    runaway.add_edge(START, "improve"); runaway.add_edge("improve", "improve")   # never ends!
    runaway.compile().invoke({"draft": "x", "attempts": 0}, {"recursion_limit": 4})
except Exception as e:
    print("\nlimit hit ->", type(e).__name__)


"""
             INPUT STATE
       draft = "start"
       attempts = 0
                  |
                  v
        +-------------------+
        |   IMPROVE NODE    |
        | Add more detail   |
        | Increase attempts |
        +-------------------+
                  |
                  v
        +-------------------+
        |  GOOD_ENOUGH?     |
        | Check conditions  |
        +-------------------+
                  |
          +-------+-------+
          |               |
      Not enough       Good enough
          |               |
          v               v
    Go back to       +-----------+
    IMPROVE NODE     |    END    |
          |          +-----------+
          |
          +---- LOOP AGAIN


    SAFETY: MAX 5 ATTEMPTS
    ----------------------
    If draft is long enough OR attempts >= 5,
    stop the loop.

    EXTRA SAFETY:
    recursion_limit = 4
    Stops a runaway graph that loops forever.
"""