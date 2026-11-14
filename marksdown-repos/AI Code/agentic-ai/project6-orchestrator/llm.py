"""Shared helpers (same as Project 5).

Adapted from Anthropic's claude-cookbooks, patterns/agents/util.py:
  llm_call()    one call to Claude, returns the text
  extract_xml() pull <tag>...</tag> out of a reply
Changes: the client is created on first use (tests need no API key), and the
model and temperature are parameters. Workers call the model from many threads
at once; the lock only guards the creation of the shared client.
"""
import os
import re
import threading

from anthropic import Anthropic

MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
WORKER_MODEL = os.environ.get("WORKER_MODEL", "claude-haiku-4-5")

_client = None
_lock = threading.Lock()


def _get_client() -> Anthropic:
    global _client
    with _lock:
        if _client is None:
            _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        return _client


def llm_call(prompt: str, system_prompt: str, model: str | None = None,
             temperature: float = 0.1, max_tokens: int = 2048) -> str:
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
