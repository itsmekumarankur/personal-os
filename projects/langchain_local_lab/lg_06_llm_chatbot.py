"""LG-06  An LLM inside a node. MessagesState + add_messages.  Run: python lg_06_llm_chatbot.py"""
from langgraph.graph import StateGraph, MessagesState, START, END
from common import get_llm

llm = get_llm()


def chatbot(state: MessagesState):
    reply = llm.invoke(state["messages"])        # the node sends the WHOLE message list
    return {"messages": [reply]}                 # add_messages APPENDS this to the list


b = StateGraph(MessagesState)                    # MessagesState = {"messages": Annotated[list, add_messages]}
b.add_node("chatbot", chatbot)
b.add_edge(START, "chatbot"); b.add_edge("chatbot", END)
graph = b.compile()

# Each .invoke() starts from the state YOU pass. No checkpointer = no memory between calls.
r1 = graph.invoke({"messages": [("user", "My name is Ankur.")]})
print("call 1:", r1["messages"][-1].text)

r2 = graph.invoke({"messages": [("user", "What is my name?")]})
print("call 2 (fresh state):", r2["messages"][-1].text)

# Memory by hand: feed the previous state's messages back in.
r3 = graph.invoke({"messages": r1["messages"] + [("user", "What is my name?")]})
print("call 3 (history passed in):", r3["messages"][-1].text)
print("\n-> Next lessons make the graph remember automatically (checkpointer).")

"""
          CALL 1
    "My name is Ankur"
             |
             v
     +------------------+
     |   LANGGRAPH      |
     |   chatbot NODE   |
     +------------------+
             |
             v
     +------------------+
     |   CLAUDE (LLM)   |
     | Generates reply |
     +------------------+
             |
             v
       "Nice to meet
          you, Ankur!"
             |
             v
       RESULT r1
    Messages saved in
    Python variable r1


          CALL 2
    "What is my name?"
             |
             v
     Fresh graph state
     (no previous chat)
             |
             v
          CLAUDE
             |
             v
    Doesn't know your name


          CALL 3
    Previous messages + 
    "What is my name?"
             |
             v
          CLAUDE
             |
             v
      "Your name is Ankur!"
"""