import os
import json
import logging
import requests
from anthropic import Anthropic

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent")

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-5"





# AI Agent Tool-Calling Flow
#
# User Request
#      |
#      v
#   Claude LLM
#      |
#      v
# Need a tool?
#   /       \
# No         Yes
# |           |
# v           v
# Answer    tool_use request
# directly    |
#             v
#       Python executes tool
#             |
#             v
#        tool_result
#             |
#             v
#        Claude LLM
#             |
#             v
#        Final Answer
#
# Key Learning:
# Claude decides WHAT to do.
# Python executes the actual tool.
# Claude uses the result to answer the user.

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
    logger.debug("Calculator called with expression: %s", expression)
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        logger.warning("Calculator rejected expression (disallowed chars): %s", expression)
        return "Error: expression contains disallowed characters."
    try:
        result = str(eval(expression, {"__builtins__": {}}))
        logger.debug("Calculator result: %s", result)
        return result
    except Exception as e:
        logger.error("Calculator eval failed: %s", e)
        return f"Error: {e}"


def run_get_weather(latitude: float, longitude: float, city_name: str) -> str:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}&current_weather=true"
    )
    logger.debug("Weather request URL: %s", url)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        temp = data["current_weather"]["temperature"]
        wind = data["current_weather"]["windspeed"]
        result = f"Weather in {city_name}: {temp}°C, wind {wind} km/h."
        logger.debug("Weather result: %s", result)
        return result
    except Exception as e:
        logger.error("Weather fetch failed: %s", e)
        return f"Error fetching weather: {e}"


TOOL_FUNCTIONS = {
    "calculator": run_calculator,
    "get_weather": run_get_weather,
}


def run_agent(user_message: str, max_turns: int = 5) -> str:
    logger.info("run_agent called | message=%r", user_message)
    messages = [{"role": "user", "content": user_message}]

    for turn in range(max_turns):
        logger.debug("Turn %d — sending %d message(s) to Claude", turn + 1, len(messages))
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                tools=tools,
                messages=messages,
            )
        except Exception as e:
            logger.exception("Claude API call failed on turn %d", turn + 1)
            raise

        logger.debug("Stop reason: %s", response.stop_reason)

        if response.stop_reason != "tool_use":
            final = "".join(
                block.text for block in response.content if block.type == "text"
            )
            logger.info("Agent finished after %d turn(s)", turn + 1)
            return final

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                logger.info("Tool call: %s | input=%s", block.name, block.input)
                fn = TOOL_FUNCTIONS.get(block.name)
                if fn is None:
                    logger.error("Unknown tool requested: %s", block.name)
                    result = f"Error: unknown tool '{block.name}'"
                else:
                    result = fn(**block.input)
                logger.debug("Tool result for %s: %s", block.name, result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})

    logger.warning("Reached max turns (%d) without a final answer", max_turns)
    return "Reached max turns without a final answer."