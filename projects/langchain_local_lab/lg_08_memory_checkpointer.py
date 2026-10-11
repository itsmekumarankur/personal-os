"""LG-08  Automatic memory with a checkpointer + thread_id.  Run: python lg_08_memory_checkpointer.py"""
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from common import get_llm

llm = get_llm()
b = StateGraph(MessagesState)
b.add_node("chatbot", lambda s: {"messages": [llm.invoke(s["messages"])]})
b.add_edge(START, "chatbot"); b.add_edge("chatbot", END)

graph = b.compile(checkpointer=InMemorySaver())      # <- the ONLY change vs LG-06

def ask(thread: str, text: str):
    out = graph.invoke({"messages": [("user", text)]}, {"configurable": {"thread_id": thread}})
    print(f"[{thread}] {text}\n[{thread}] -> {out['messages'][-1].text}\n")

ask("t1", "My name is Ankur.")
ask("t1", "What is my name?")        # remembered: same thread, state restored automatically
ask("t2", "What is my name?")        # different thread = empty state = doesn't know

# Peek inside: the saved state of thread t1
snap = graph.get_state({"configurable": {"thread_id": "t1"}})
print("t1 saved messages:", len(snap.values["messages"]))
print("next node to run :", snap.next)       # () means the run finished


"""
          FIRST QUESTION (thread t1)
             "My name is Ankur"
                      |
                      v
              +----------------+
              |    CHATBOT     |
              |  Claude replies|
              +----------------+
                      |
                      v
              +----------------+
              |  CHECKPOINTER  |
              | Saves messages |
              | for thread t1  |
              +----------------+


          SECOND QUESTION (thread t1)
             "What is my name?"
                      |
                      v
              +----------------+
              |  CHECKPOINTER  |
              | Restores old   |
              | conversation   |
              +----------------+
                      |
                      v
              +----------------+
              |    CLAUDE      |
              | Reads old +    |
              | new messages   |
              +----------------+
                      |
                      v
                 "Your name
                  is Ankur!"


          THIRD QUESTION (thread t2)
             "What is my name?"
                      |
                      v
              +----------------+
              |  CHECKPOINTER  |
              | No history for |
              | thread t2      |
              +----------------+
                      |
                      v
              +----------------+
              |    CLAUDE      |
              | Has no name    |
              | from this chat |
              +----------------+
                      |
                      v
              "I don't know
               your name."
"""