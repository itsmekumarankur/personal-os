"""Shared helpers (same as Project 6, with an EVAL_MODEL setting).

Adapted from Anthropic's claude-cookbooks, patterns/agents/util.py:
  llm_call()    one call to Claude, returns the text
  extract_xml() pull <tag>...</tag> out of a reply
Changes: the client is created on first use (tests need no API key), and the
model, temperature and token limit are parameters.
"""
import os
import re

from anthropic import Anthropic

MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
EVAL_MODEL = os.environ.get("EVAL_MODEL", MODEL)     # set to a different model to avoid a model grading itself

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def llm_call(prompt: str, system_prompt: str, model: str | None = None,
             temperature: float = 0.1, max_tokens: int = 1500) -> str:
    response = _get_client().messages.create(
        model=model or MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.content[0].text


def extract_xml(text: str, tag: str) -> str:
    match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""
