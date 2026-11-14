"""LG-03  Reducers: what happens when two nodes write the SAME key?  No LLM.  Run: python lg_03_reducers.py"""
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# A) No reducer -> the last write simply OVERWRITES.
class Overwrite(TypedDict):
    log: list[str]

# B) With a reducer -> new values are COMBINED with old ones (operator.add on lists = append).
class Append(TypedDict):
    log: Annotated[list[str], operator.add]


def build(schema):
    b = StateGraph(schema)
    b.add_node("a", lambda s: {"log": ["step A ran"]})
    b.add_node("b", lambda s: {"log": ["step B ran"]})
    b.add_edge(START, "a"); b.add_edge("a", "b"); b.add_edge("b", END)
    return b.compile()


print("without reducer:", build(Overwrite).invoke({"log": []}))
print("with reducer   :", build(Append).invoke({"log": []}))

# C) add_messages is the built-in reducer for chat history: appends, and merges by message id.
from langchain_core.messages import HumanMessage, AIMessage
merged = add_messages([HumanMessage("hi", id="1")], [AIMessage("hello", id="2")])
print("\nadd_messages ->", [(m.type, m.content) for m in merged])


"""
       START: log = []
              |
              v
       +--------------+
       |   NODE A     |
       | Writes:      |
       | ["step A ran"]|
       +--------------+
              |
              v
       +--------------+
       |   NODE B     |
       | Writes:      |
       | ["step B ran"]|
       +--------------+
              |
              v
        WHICH RULE?
              |
       +------+------+
       |             |
       v             v
  NO REDUCER     WITH REDUCER
  (Overwrite)    (operator.add)
       |             |
       v             v
  ["step B ran"] ["step A ran",
                  "step B ran"]
       |             |
       v             v
  A's value lost   Both values kept

Concept. By default a write overwrites. A reducer function tells LangGraph how to COMBINE old and new values instead.

New things in this step
- Why parallel nodes need reducers?

Architecture view. The reducer sits between a node's return value and the stored state. 
                   This is the rule for merging agent outputs.
"""