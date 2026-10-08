"""The only place that calls Claude. Tests replace create_message().

Operational settings that matter in production: a timeout (a hung call must not hold a request
forever) and a small number of automatic retries for temporary errors.
"""
import os

from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=30.0, max_retries=2)
    return _client


def create_message(system: str, messages: list, tools: list, model: str,
                   temperature: float = 0.0, max_tokens: int = 1024):
    return _get_client().messages.create(
        model=model, max_tokens=max_tokens, system=system, messages=messages,
        tools=tools, temperature=temperature,
    )
