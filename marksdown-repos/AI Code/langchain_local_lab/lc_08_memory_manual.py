"""LC-08  The TRUTH about memory: the model has none. You resend the history.  Run: python lc_08_memory_manual.py"""
from langchain_core.messages import SystemMessage, HumanMessage
from common import get_llm

llm = get_llm()

print("=== WITHOUT memory: each call is a fresh universe ===")
llm.invoke("My name is Ankur.")
print("AI:", llm.invoke("What is my name?").text)

print("\n=== WITH memory: we keep a list and resend it every time ===")
history = [SystemMessage("You are a concise assistant.")]

for user_text in ["My name is Ankur and I live in Chennai.", "What is my name and where do I live?"]:
    history.append(HumanMessage(user_text))
    ai = llm.invoke(history)          # the WHOLE list goes to the model
    history.append(ai)                # remember the answer too
    print(f"You: {user_text}\nAI : {ai.text}\n[messages sent this turn: {len(history) - 1}]\n")


"""
Concept:
    - The model remembers nothing between calls. 
    - 'Memory' is just you keeping a list and sending all of it every time.

New things in this step

Call 1 vs call 2 without history
Appending HumanMessage and the AIMessage to a list
Counting messages sent per turn: the cost grows each turn
Architecture view. Memory lives in your process (a Python list). The model is stateless. Every turn re-sends everything.
"""