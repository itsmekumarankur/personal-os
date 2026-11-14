"""LG-14  Subgraphs: an agent inside an agent, and how state crosses the boundary.  No LLM.  Run: python lg_14_subgraph.py"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ---------- CHILD graph (a mini "research agent") with a PRIVATE key ----------
class ChildState(TypedDict):
    question: str
    facts: list[str]          # private scratchpad - parent never declares it
    answer: str

def find_facts(s: ChildState): return {"facts": [f"fact-1 about {s['question']}", f"fact-2 about {s['question']}"]}
def summarize(s: ChildState): return {"answer": f"Summary built from {len(s['facts'])} private facts."}

cb = StateGraph(ChildState)
cb.add_node("find_facts", find_facts); cb.add_node("summarize", summarize)
cb.add_edge(START, "find_facts"); cb.add_edge("find_facts", "summarize"); cb.add_edge("summarize", END)
child = cb.compile()


# ---------- PATTERN 1: shared keys -> add the compiled child directly as a node ----------
class ParentState(TypedDict):
    question: str
    answer: str

pb = StateGraph(ParentState)
pb.add_node("research", child)                                   # keys with the same name (question, answer) flow automatically
pb.add_node("polish", lambda s: {"answer": s["answer"].upper()})
pb.add_edge(START, "research"); pb.add_edge("research", "polish"); pb.add_edge("polish", END)
print("PATTERN 1 result:", pb.compile().invoke({"question": "UPI"}))     # note: no 'facts' key leaked to the parent


# ---------- PATTERN 2: DIFFERENT schemas -> wrap the child in a function that translates state ----------
class OtherChild(TypedDict):
    query: str
    result: str

ob = StateGraph(OtherChild)
ob.add_node("work", lambda s: {"result": f"result for '{s['query']}'"})
ob.add_edge(START, "work"); ob.add_edge("work", END)
other_child = ob.compile()

def call_other_child(state: ParentState):
    out = other_child.invoke({"query": state["question"]})     # parent -> child mapping
    return {"answer": out["result"]}                           # child -> parent mapping

wb = StateGraph(ParentState)
wb.add_node("adapter", call_other_child)
wb.add_edge(START, "adapter"); wb.add_edge("adapter", END)
print("PATTERN 2 result:", wb.compile().invoke({"question": "NEFT"}))


"""
          PARENT GRAPH
       Question: "UPI"
                |
                v
      +--------------------+
      |   CHILD GRAPH      |
      |  find_facts        |
      |  Finds 2 facts     |
      +--------------------+
                |
                v
      +--------------------+
      |   summarize        |
      |  Uses 2 facts      |
      |  Creates answer    |
      +--------------------+
                |
                v
       Answer returns to parent
       (private facts stay inside)
                |
                v
      +--------------------+
      |   polish NODE      |
      |  Converts answer   |
      |  to UPPERCASE      |
      +--------------------+
                |
                v
          FINAL ANSWER


   PATTERN 2: DIFFERENT KEY NAMES
   --------------------------------
   Parent question
        |
        v
   Adapter converts:
   question -> query
        |
        v
   Child graph processes query
        |
        v
   Child returns: result
        |
        v
   Adapter converts:
   result -> answer
        |
        v
   Parent receives answer
"""