"""Prompt chaining: draft -> critique -> polish.

Adapted from Anthropic's claude-cookbooks, patterns/agents:
  - util.py                 -> llm_call() and extract_xml()
  - basic_workflows.ipynb   -> the prompt-chaining idea: each step's output
                               becomes input to the next step

What is added here: a context that carries the request AND earlier outputs
(polish needs both the draft and the critique), per-step temperature, and a
programmatic gate that skips the polish step when the critique says "pass".
"""
import os
import re
from dataclasses import asdict, dataclass

from anthropic import Anthropic

MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
SYSTEM_PROMPT = (
    "You are a careful writing assistant. "
    "Follow the output format you are given exactly."
)

_client = None


def _get_client() -> Anthropic:
    # Created on first use so tests can run without an API key.
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def llm_call(prompt: str, system_prompt: str = SYSTEM_PROMPT, model: str | None = None,
             temperature: float = 0.1) -> str:
    """One call to Claude; returns the text of the reply (cookbook util.py)."""
    response = _get_client().messages.create(
        model=model or MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.content[0].text


def extract_xml(text: str, tag: str) -> str:
    """Return the content of <tag>...</tag>, or "" if the tag is missing (cookbook util.py)."""
    match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1) if match else ""


@dataclass
class Step:
    name: str
    instruction: str
    temperature: float


DRAFT = Step(
    name="draft",
    temperature=0.7,
    instruction=(
        "Write a first draft that fulfils the request.\n"
        "Audience: {audience}.\n"
        "Keep it under {max_words} words.\n"
        "Put the draft inside <draft></draft> tags and write nothing outside them."
    ),
)

CRITIQUE = Step(
    name="critique",
    temperature=0.2,
    instruction=(
        "You are a demanding editor. Review the draft against the request and the audience ({audience}).\n"
        "List at most 5 concrete problems (accuracy, clarity, structure, tone, length), "
        "each with a specific fix.\n"
        "Then give a verdict: 'pass' if the draft needs no meaningful changes, otherwise 'revise'.\n"
        "Format exactly:\n"
        "<critique>your numbered problems and fixes</critique>\n"
        "<verdict>pass or revise</verdict>"
    ),
)

POLISH = Step(
    name="final",
    temperature=0.3,
    instruction=(
        "Rewrite the draft, applying every fix from the critique. "
        "Keep what already works. Keep it under {max_words} words.\n"
        "Put only the final text inside <final></final> tags."
    ),
)


@dataclass
class PipelineResult:
    final: str
    draft: str
    critique: str
    verdict: str
    steps_run: int


def _run_step(step: Step, context: dict, params: dict, llm) -> str:
    """Build the prompt from everything so far, then call the model."""
    blocks = "\n\n".join(f"<{key}>\n{value}\n</{key}>" for key, value in context.items())
    prompt = f"{blocks}\n\n{step.instruction.format(**params)}"
    return llm(prompt, SYSTEM_PROMPT, temperature=step.temperature)


def run_pipeline(task: str, audience: str = "a general reader", max_words: int = 200,
                 llm=None) -> dict:
    llm = llm or llm_call          # looked up at call time so tests can swap it
    params = {"audience": audience, "max_words": max_words}
    context = {"request": task}

    # Step 1: draft
    raw = _run_step(DRAFT, context, params, llm)
    draft = extract_xml(raw, "draft").strip() or raw.strip()
    context["draft"] = draft

    # Step 2: critique
    raw = _run_step(CRITIQUE, context, params, llm)
    critique = extract_xml(raw, "critique").strip() or raw.strip()
    verdict = extract_xml(raw, "verdict").strip().lower()
    context["critique"] = critique

    # Gate: a plain Python check between steps decides whether to continue.
    if verdict == "pass":
        return asdict(PipelineResult(draft, draft, critique, verdict, steps_run=2))

    # Step 3: polish
    raw = _run_step(POLISH, context, params, llm)
    final = extract_xml(raw, "final").strip() or raw.strip()
    return asdict(PipelineResult(final, draft, critique, verdict or "revise", steps_run=3))
