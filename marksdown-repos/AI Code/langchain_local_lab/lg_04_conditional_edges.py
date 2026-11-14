"""LG-04  Branching: the graph decides where to go next.  No LLM.  Run: python lg_04_conditional_edges.py"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    amount: float
    decision: str


def check(state: State):
    print(f"  [check] amount = {state['amount']}")
    return {}                                    # nothing to change; routing happens on the edge


def route(state: State) -> str:                  # the ROUTER returns the NAME of the next path
    if state["amount"] <= 10_000:   return "auto"
    if state["amount"] <= 100_000:  return "manager"
    return "reject"


b = StateGraph(State)
b.add_node("check", check)
b.add_node("auto_approve",    lambda s: {"decision": "approved automatically"})
b.add_node("manager_review",  lambda s: {"decision": "sent to manager for review"})
b.add_node("reject",          lambda s: {"decision": "rejected: above limit"})

b.add_edge(START, "check")
b.add_conditional_edges("check", route, {"auto": "auto_approve", "manager": "manager_review", "reject": "reject"})
for n in ("auto_approve", "manager_review", "reject"):
    b.add_edge(n, END)
graph = b.compile()

for amt in [2_500, 45_000, 750_000]:
    print(amt, "->", graph.invoke({"amount": amt})["decision"])


"""
             INPUT
       amount = ₹2,500
                |
                v
        +----------------+
        |   CHECK NODE   |
        | Read amount    |
        +----------------+
                |
                v
        +----------------+
        |  ROUTER        |
        | Which path?    |
        +----------------+
                |
       +--------+---------+
       |        |         |
    <= ₹10K  <= ₹1 lakh  > ₹1 lakh
       |        |         |
       v        v         v
  +---------+ +---------+ +---------+
  | AUTO    | | MANAGER | | REJECT  |
  | APPROVE | | REVIEW  | |         |
  +---------+ +---------+ +---------+
       |        |         |
       v        v         v
      END      END       END
"""