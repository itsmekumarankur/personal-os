"""
LG-09  Persistent memory in SQLite + time travel.  Run it TWICE:
    python lg_09_memory_sqlite.py "My name is Ankur and I lead a wealth platform."
    python lg_09_memory_sqlite.py "What do I lead?"
"""
import sqlite3, sys
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from common import get_llm

llm = get_llm()
b = StateGraph(MessagesState)
b.add_node("chatbot", lambda s: {"messages": [llm.invoke(s["messages"])]})
b.add_edge(START, "chatbot"); b.add_edge("chatbot", END)

text = sys.argv[1] if len(sys.argv) > 1 else "What do you remember about me?"
cfg = {"configurable": {"thread_id": "ankur-main"}}

with SqliteSaver.from_conn_string("graph_memory.db") as saver:     # a checkpointer that writes to a .db file
    graph = b.compile(checkpointer=saver)
    out = graph.invoke({"messages": [("user", text)]}, cfg)
    print("You:", text)
    print("AI :", out["messages"][-1].text)

    history = list(graph.get_state_history(cfg))                    # every saved checkpoint, newest first
    print(f"\n{len(history)} checkpoints saved for this thread:")
    for snap in history:
        print(f"  step={snap.metadata.get('step'):>2} | messages={len(snap.values.get('messages', []))} | next={snap.next}")

print("\n--- tables LangGraph created inside graph_memory.db ---")
con = sqlite3.connect("graph_memory.db")
for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(" ", name, "->", con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0], "rows")


"""
       FIRST RUN
  "My name is Ankur and
   I lead a wealth platform."
              |
              v
      +------------------+
      |     CHATBOT      |
      |  Claude answers  |
      +------------------+
              |
              v
      +------------------+
      |   SQLite DB      |
      | graph_memory.db  |
      | Saves conversation|
      +------------------+
              |
              v
       PROGRAM ENDS


       SECOND RUN
     "What do I lead?"
              |
              v
      +------------------+
      |     CHATBOT      |
      | Same thread_id   |
      | "ankur-main"     |
      +------------------+
              |
              v
      +------------------+
      |   SQLite DB      |
      | Loads old chat   |
      | history          |
      +------------------+
              |
              v
      +------------------+
      |     CLAUDE       |
      | Reads old + new  |
      | messages         |
      +------------------+
              |
              v
   "You lead a wealth platform!"
"""