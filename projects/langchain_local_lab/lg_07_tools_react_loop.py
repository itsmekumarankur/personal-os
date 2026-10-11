"""LG-07  Build the ReAct agent loop by hand: agent <-> tools, with a SQLite tool.  Run: python lg_07_tools_react_loop.py"""
import sqlite3
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from common import get_llm, ensure_demo_db

DB = ensure_demo_db()


@tool
def query_shop_db(sql: str) -> str:
    """Run a read-only SELECT on SQLite. Tables: products(id,name,price,stock), orders(id,product_id,qty,city)."""
    if not sql.strip().lower().startswith("select"):
        return "Only SELECT is allowed."
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return str(con.execute(sql).fetchall())
    except Exception as e:
        return f"SQL error: {e}"


tools = [query_shop_db]
llm_with_tools = get_llm().bind_tools(tools)


def agent(state: MessagesState):                                   # NODE 1: the brain (LLM decides)
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


b = StateGraph(MessagesState)
b.add_node("agent", agent)
b.add_node("tools", ToolNode(tools))                               # NODE 2: the hands (runs tool_calls, appends ToolMessages)
b.add_edge(START, "agent")
b.add_conditional_edges("agent", tools_condition)                  # tool_calls present? -> "tools" ; else -> END
b.add_edge("tools", "agent")                                       # <- THE LOOP: results go back to the brain
graph = b.compile()

question = "Which product has the highest total quantity ordered, and what is its price?"
for step in graph.stream({"messages": [("user", question)]}, stream_mode="values"):
    step["messages"][-1].pretty_print()


"""
       USER ASKS A QUESTION
  "Which product has the highest
   quantity ordered, and its price?"
                |
                v
       +--------------------+
       |    AGENT (BRAIN)   |
       |   Claude decides  |
       |   what SQL to use |
       +--------------------+
                |
                v
       +--------------------+
       |   TOOLS (HANDS)    |
       | query_shop_db()    |
       | Runs SQL on SQLite |
       +--------------------+
                |
                v
       +--------------------+
       |   DATABASE RESULT  |
       | Returns query rows |
       +--------------------+
                |
                v
       +--------------------+
       |    AGENT (BRAIN)   |
       | Reads the results  |
       | Is more work needed?|
       +--------------------+
                |
          +-----+-----+
          |           |
     Need more?    Finished?
          |           |
          v           v
     Call tool    FINAL ANSWER
          |       to the user
          |
          +----> AGENT again
"""