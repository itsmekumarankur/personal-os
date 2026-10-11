"""LG-13  Multi-agent #2: a SUPERVISOR routes work with Command(goto=...).  Run: python lg_13_supervisor_handoff.py"""
from typing import Literal
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from common import get_llm

llm = get_llm()


class Route(BaseModel):
    next: Literal["math_agent", "writer_agent", "FINISH"]


class State(MessagesState):
    turns: int                                           # extra key: loop guard


router_llm = llm.with_structured_output(Route)           # build once; the model must answer in the Route schema


def transcript(state: State) -> str:                    # flatten messages -> one block of text (works with every model)
    return "\n".join(f"{getattr(m, 'name', None) or m.type}: {m.content}" for m in state["messages"])


def supervisor(state: State) -> Command[Literal["math_agent", "writer_agent", "__end__"]]:
    turns = state.get("turns", 0)
    if turns >= 4:
        return Command(goto=END)
    decision = router_llm.invoke([
        SystemMessage("You supervise two workers: math_agent (calculations) and writer_agent (friendly wording). "
                      "Read the conversation. Pick who should act next, or FINISH when the user's request is fully answered."),
        HumanMessage(transcript(state)),
    ])
    print(f"  [supervisor] turn {turns}: next = {decision.next}")
    if decision.next == "FINISH":
        return Command(goto=END)
    return Command(goto=decision.next, update={"turns": turns + 1})      # goto = HANDOFF, update = state change


def make_worker(name: str, role: str):
    def worker(state: State) -> Command[Literal["supervisor"]]:
        text = llm.invoke([SystemMessage(role), HumanMessage(transcript(state))]).text
        return Command(goto="supervisor", update={"messages": [AIMessage(content=text, name=name)]})   # report back
    return worker


b = StateGraph(State)
b.add_node("supervisor", supervisor)
b.add_node("math_agent", make_worker("math_agent", "You do calculations. Show the result briefly."))
b.add_node("writer_agent", make_worker("writer_agent", "You write the final friendly reply for the user using results already in the conversation."))
b.add_edge(START, "supervisor")                          # note: NO other edges - Command(goto=...) creates the routing at runtime
graph = b.compile()

out = graph.invoke({"messages": [("user", "My bill is Rs. 2,450 and I want to tip 12%. Tell me the total in a friendly sentence.")], "turns": 0})
print("\nFINAL CONVERSATION:\n" + transcript(out))


"""
           USER ASKS A QUESTION
     "Bill ₹2,450 + 12% tip. Tell me
             the total nicely."
                    |
                    v
          +--------------------+
          |    SUPERVISOR      |
          | Decides who works  |
          | next               |
          +--------------------+
                    |
             Routes using
           Command(goto=...)
                    |
                    v
          +--------------------+
          |    MATH AGENT      |
          | Calculates tip     |
          | ₹2,450 × 12% = ₹294|
          | Total = ₹2,744     |
          +--------------------+
                    |
                    v
          +--------------------+
          |    SUPERVISOR      |
          | Chooses next worker|
          +--------------------+
                    |
                    v
          +--------------------+
          |   WRITER AGENT     |
          | Writes a friendly  |
          | sentence using     |
          | the calculation    |
          +--------------------+
                    |
                    v
          +--------------------+
          |    SUPERVISOR      |
          | Request answered?  |
          +--------------------+
                    |
                    v
                  FINISH
                    |
                    v
     "Your total is ₹2,744, including
       a ₹294 tip. Thanks!"
"""