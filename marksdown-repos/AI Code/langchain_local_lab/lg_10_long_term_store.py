"""LG-10  Short-term vs LONG-term memory: the Store shares facts ACROSS threads.  Run: python lg_10_long_term_store.py"""
import uuid
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from common import get_llm

llm = get_llm()


def chatbot(state: MessagesState, config: RunnableConfig, *, store: BaseStore):    # LangGraph injects `store`
    ns = (config["configurable"]["user_id"], "memories")           # namespace = like a folder per user
    last = state["messages"][-1].content
    if isinstance(last, str) and last.lower().startswith("remember:"):
        store.put(ns, str(uuid.uuid4()), {"fact": last.split(":", 1)[1].strip()})   # WRITE long-term memory
    facts = [item.value["fact"] for item in store.search(ns)]                        # READ long-term memory
    system = "Facts you know about the user:\n- " + "\n- ".join(facts) if facts else "You know nothing about the user yet."
    return {"messages": [llm.invoke([SystemMessage(system)] + state["messages"])]}


b = StateGraph(MessagesState)
b.add_node("chatbot", chatbot)
b.add_edge(START, "chatbot"); b.add_edge("chatbot", END)

store = InMemoryStore()                                            # swap for a Postgres-backed store in production
graph = b.compile(checkpointer=InMemorySaver(), store=store)       # checkpointer = per-THREAD memory ; store = per-USER memory


def run(thread: str, text: str):
    cfg = {"configurable": {"thread_id": thread, "user_id": "ankur"}}
    print(f"[{thread}] {text}\n  -> {graph.invoke({'messages': [('user', text)]}, cfg)['messages'][-1].text}\n")


run("monday",  "remember: I prefer very short answers and I code in Python.")
run("friday",  "What language do I code in?")        # NEW thread, no chat history - yet it knows, via the store

print("raw store contents:", [(i.namespace, i.value) for i in store.search(("ankur", "memories"))])


"""
          MONDAY: USER SHARES A FACT
     "Remember: I code in Python"
                    |
                    v
        +-----------------------+
        |      CHATBOT          |
        | Reads user's message  |
        +-----------------------+
                    |
                    v
        +-----------------------+
        |   LONG-TERM STORE     |
        | Saves:                 |
        | "I code in Python"    |
        +-----------------------+


          FRIDAY: NEW CONVERSATION
     "What language do I code in?"
                    |
                    v
        +-----------------------+
        |      CHATBOT          |
        | Reads the question    |
        +-----------------------+
                    |
                    v
        +-----------------------+
        |   LONG-TERM STORE     |
        | Retrieves saved fact  |
        +-----------------------+
                    |
                    v
        +-----------------------+
        |        CLAUDE         |
        | Gets the fact +       |
        | user's question       |
        +-----------------------+
                    |
                    v
             "You code in Python!"
"""