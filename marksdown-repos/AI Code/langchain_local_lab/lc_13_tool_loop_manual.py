"""LC-13  Tool calling, part 2: the loop that every agent framework hides.  Run: python lc_13_tool_loop_manual.py"""
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from common import get_llm


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"It is 31C and humid in {city}."


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


tools = [get_weather, multiply]
tools_by_name = {t.name: t for t in tools}
llm = get_llm().bind_tools(tools)

messages = [HumanMessage("What's the weather in Chennai, and what is 12.5 times 8?")]

for step in range(1, 6):                                   # safety cap: never loop forever
    ai = llm.invoke(messages)                              # 1) ask the model
    messages.append(ai)
    if not ai.tool_calls:                                  # 2) no tool requested -> it is the final answer
        print(f"\nstep {step}: FINAL ANSWER -> {ai.text}")
        break
    for call in ai.tool_calls:                             # 3) otherwise run every requested tool
        print(f"step {step}: model asked for {call['name']}({call['args']})")
        result = tools_by_name[call["name"]].invoke(call["args"])
        print(f"         tool returned {result!r}")
        messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))   # 4) report back, loop again

print("\nmessage trail:", [m.type for m in messages])    # human, ai, tool, tool, ai


"""
Concept:
     Ask the model, run what it requests, send the result back as a ToolMessage, repeat until it answers in plain text.

New things in this step

ToolMessage with tool_call_id
The stop condition: no more tool_calls
A max-step guard so a confused model cannot loop forever
Architecture view. This ask-act-observe loop is the core of every agent framework. LangGraph (LG-07) draws it as two nodes and one edge.
"""