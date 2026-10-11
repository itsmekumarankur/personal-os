"""LG-15  Human-in-the-loop: pause the graph, wait for a human, resume.  No LLM.  Run: python lg_15_human_in_the_loop.py"""
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class State(TypedDict):
    to: str
    amount: float
    status: str


def validate(s: State):
    print("  [validate] checks passed")
    return {"status": "validated"}


def approval(s: State):
    # interrupt() PAUSES here and saves the state. The value inside is shown to the human.
    decision = interrupt({"question": f"Approve transfer of Rs.{s['amount']:,.0f} to {s['to']}?"})
    return {"status": "approved" if decision == "yes" else "rejected by human"}


def execute(s: State):
    print("  [execute] money moved!")
    return {"status": "executed"}


def after_approval(s: State) -> str:
    return "execute" if s["status"] == "approved" else "stop"


b = StateGraph(State)
b.add_node("validate", validate); b.add_node("approval", approval); b.add_node("execute", execute)
b.add_edge(START, "validate"); b.add_edge("validate", "approval")
b.add_conditional_edges("approval", after_approval, {"execute": "execute", "stop": END})
b.add_edge("execute", END)
graph = b.compile(checkpointer=InMemorySaver())          # interrupts REQUIRE a checkpointer (state must be saved while waiting)


def run(thread: str, human_answer: str):
    cfg = {"configurable": {"thread_id": thread}}
    first = graph.invoke({"to": "Vendor Acme", "amount": 250000}, cfg)
    print(f"\n[{thread}] graph paused. It asks:", first["__interrupt__"][0].value["question"])
    print(f"[{thread}] human answers: {human_answer!r}")
    final = graph.invoke(Command(resume=human_answer), cfg)      # resume = the return value of interrupt()
    print(f"[{thread}] final status:", final["status"])


run("txn-1", "yes")
run("txn-2", "no")


"""
       START: Transfer request
       Vendor Acme: Rs. 2,50,000
                  |
                  v
          +----------------+
          |    VALIDATE    |
          | Check request  |
          +----------------+
                  |
                  v
          +----------------+
          |    APPROVAL    |
          | Pause graph    |
          | Ask a human    |
          +----------------+
                  |
                  v
          HUMAN DECIDES
                  |
           +------+------+
           |             |
        YES              NO
           |             |
           v             v
    +-------------+  +-------------+
    |   EXECUTE   |  |    STOP     |
    | Move money  |  | Reject      |
    +-------------+  +-------------+
           |             |
           v             v
     "executed"    "rejected by human"
"""