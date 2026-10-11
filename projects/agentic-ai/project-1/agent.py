import os
import json
import requests
from anthropic import Anthropic


client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-5"





## **basic AI Agent with tool calling**. 

# The important idea is that **Claude is not directly executing Python functions or calling APIs**. 
# Instead, you give Claude a list of tools it *is allowed to use*. 


# Claude looks at the user's request and decides whether it can answer directly or needs a tool. 
# If it needs a tool, Claude returns a structured `tool_use` request such as *“call `calculator` with expression `12 * 5`”*. 


# Your Python code then acts as the **orchestrator**: it identifies the requested tool, executes the actual function, takes the result, and sends that result back to Claude as a `tool_result`. 
# Claude then uses that tool output to produce the final natural-language answer. 

# So the overall pattern is **User → LLM → Tool Decision → Your Code Executes Tool → Tool Result → LLM → Final Answer**. 
# This is the fundamental **LLM tool-calling / agent loop** that you'll see repeatedly when building AI agents.


# ============================================================
# SIMPLE AGENT FLOW
# ============================================================
#
#                  USER
#                    |
#                    v
#              +-----------+
#              |  Claude   |
#              |   LLM     |
#              +-----+-----+
#                    |
#              Understands request
#                    |
#             Need a tool?
#              /          \
#            NO            YES
#             |             |
#             v             v
#       Final Answer    tool_use request
#                           |
#                           v
#                    +-------------+
#                    | Python Code |
#                    | Orchestrator|
#                    +------+------+
#                           |
#                    Execute tool
#                           |
#                 +---------+---------+
#                 |                   |
#            Calculator          Weather API
#                 |                   |
#                 +---------+---------+
#                           |
#                      Tool Result
#                           |
#                           v
#                    Send result to
#                       Claude
#                           |
#                           v
#                     Final Answer
#
#
# KEY IDEA:
#
#   Claude (LLM)  -> DECIDES what to do
#   Python        -> EXECUTES the decision
#   Tool          -> DOES the actual work
#
# ============================================================


tools = [
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. '12 * (4 + 2)'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "The math expression to evaluate"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_weather",
        "description": "Get current weather for a city using latitude and longitude.",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "city_name": {"type": "string", "description": "City name, for the response label"}
            },
            "required": ["latitude", "longitude", "city_name"]
        }
    }
]


def run_calculator(expression: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Error: expression contains disallowed characters."
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"Error: {e}"


def run_get_weather(latitude: float, longitude: float, city_name: str) -> str:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}&current_weather=true"
    )
    resp = requests.get(url, timeout=10)
    data = resp.json()
    temp = data["current_weather"]["temperature"]
    wind = data["current_weather"]["windspeed"]
    return f"Weather in {city_name}: {temp}°C, wind {wind} km/h."


TOOL_FUNCTIONS = {
    "calculator": run_calculator,
    "get_weather": run_get_weather,
}


def run_agent(user_message: str, max_turns: int = 5) -> str:
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(
                block.text for block in response.content if block.type == "text"
            )

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                fn = TOOL_FUNCTIONS[block.name]
                result = fn(**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})

    return "Reached max turns without a final answer."