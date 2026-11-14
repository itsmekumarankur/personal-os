"""LC-01  Your first model call.  Run: python lc_01_hello_llm.py"""
from langchain_core.messages import SystemMessage, HumanMessage
from common import get_llm

llm = get_llm()

# 1) Simplest call: a plain string becomes ONE human message.
reply = llm.invoke("In one sentence, what is LangChain?")
print("type    :", type(reply).__name__)      # AIMessage - the model's answer is an object, not a string
print("text    :", reply.text)
print("tokens  :", reply.usage_metadata)      # input/output token counts

# 2) Real apps send a LIST of messages: system rules + user input.
messages = [
    SystemMessage("You are a pirate. Reply in one short sentence."),
    HumanMessage("Explain what an API is."),
]
print("\nwith system message:", llm.invoke(messages).text)


"""
    Concept. A chat model is an object with .invoke(). You send messages in, you get an AIMessage back (not a plain string).

    New things in this step

    - invoke() with a plain string vs a list of messages
    - SystemMessage (rules) vs HumanMessage (user input)
    - AIMessage fields: .text, .usage_metadata (token counts)

    System message holds the standing rules for the model: its role, tone, format, and limits. It’s set by you, the developer, and the end user normally never sees it. For example: “You are a bank teller. Answer in two short sentences.”
    Human message is the actual input from the user for this turn: “What is a demat account?”
    The model reads both, but treats the system message as higher-priority instructions about how to behave, and the human message as the thing to respond to. That’s why the same question gets very different answers if you only change the system message. 


    Architecture view. Your script -> model API (cloud). One request, one response. 
    Nothing is stored anywhere.
"""