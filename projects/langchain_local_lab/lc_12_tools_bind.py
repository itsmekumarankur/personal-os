"""LC-12  Tool calling, part 1: the model only ASKS for a tool. It never runs it.  Run: python lc_12_tools_bind.py"""
from langchain_core.tools import tool
from common import get_llm


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""          # <- this docstring is what the model reads!
    return f"It is 31C and humid in {city}."


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


# 1) A tool is just a function + a name + a description + a JSON schema.
print("name       :", get_weather.name)
print("description:", get_weather.description)
print("schema     :", get_weather.args)

# 2) You can call it yourself like normal code.
print("\ndirect call:", get_weather.invoke({"city": "Chennai"}), "|", multiply.invoke({"a": 12.5, "b": 8}))

# 3) Give the tools to the model. It answers with a REQUEST, not a result.
llm_with_tools = get_llm().bind_tools([get_weather, multiply])
ai = llm_with_tools.invoke("What's the weather in Chennai?")
print("\nmodel text    :", repr(ai.text))
print("model wants   :", ai.tool_calls)       # [{'name': 'get_weather', 'args': {'city': 'Chennai'}, 'id': '...'}]
print("(nothing was executed - YOU must run the tool and report back; see LC-13)")


"""
Concept:
     A tool is a function plus a name, a description and an argument schema. 
     The model sees the description and may ask you to run it.

New things in this step

The @tool decorator and the docstring as the model's instructions
tool.name / .description / .args
llm.bind_tools([...]) and ai.tool_calls
Architecture view. Model returns a REQUEST (name + args + id). No code has run. Your program is the one that executes the function.
"""