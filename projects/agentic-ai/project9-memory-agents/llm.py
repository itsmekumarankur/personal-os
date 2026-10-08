"""One place that talks to Claude (messages API with tools).

Same idea as the util.py helper in Anthropic's claude-cookbooks (patterns/agents), but it returns
the whole response because the agents here use tools. The client is created on first use, so tests
need no API key and tests can replace create_message().
"""
import os

from anthropic import Anthropic

MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def create_message(system: str, messages: list, tools: list | None = None,
                   model: str | None = None, temperature: float = 0.2, max_tokens: int = 1500):
    kwargs = dict(model=model or MODEL, max_tokens=max_tokens, system=system,
                  messages=messages, temperature=temperature)
    if tools:
        kwargs["tools"] = tools
    return _get_client().messages.create(**kwargs)
