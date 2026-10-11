"""
Prompt chaining: draft -> critique -> polish.

Simple idea:

    User Request
         |
         v
      DRAFT
         |
         v
     CRITIQUE
         |
      +--+--+
      |     |
    pass   revise
      |     |
    FINAL  POLISH
             |
             v
           FINAL

Each step uses the output of the previous step.
"""

import os
import re
from dataclasses import asdict, dataclass

from anthropic import Anthropic


# Model can be changed using the MODEL environment variable.
MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")

SYSTEM_PROMPT = (
    "You are a careful writing assistant. "
    "Follow the output format you are given exactly."
)

_client = None


def _get_client() -> Anthropic:
    # Create the Claude client only when it is actually needed.
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def llm_call(
    prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
    model: str | None = None
) -> str:
    """Call Claude once and return its text response."""

    response = _get_client().messages.create(
        model=model or MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )

    text = "".join(
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
        and isinstance(getattr(block, "text", None), str)
    )
    if not text:
        block_types = [getattr(block, "type", "unknown") for block in response.content]
        raise RuntimeError(
            "Claude response contained no text blocks "
            f"(stop_reason={response.stop_reason!r}, block_types={block_types!r})"
        )

    return text


def extract_xml(text: str, tag: str) -> str:
    # Get only the text inside <tag>...</tag>.
    match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1) if match else ""


@dataclass
class Step:
    name: str
    instruction: str


# Step 1: Ask the LLM to create a first draft.
DRAFT = Step(
    name="draft",
    instruction=(
        "Write a first draft that fulfils the request.\n"
        "Audience: {audience}.\n"
        "Keep it under {max_words} words.\n"
        "Put the draft inside <draft></draft> tags and write nothing outside them."
    ),
)


# Step 2: Ask another LLM call to find problems in the draft.
CRITIQUE = Step(
    name="critique",
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


# Step 3: If critique says "revise", improve the draft.
POLISH = Step(
    name="final",
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
    # Send the previous outputs + current instruction to the LLM.
    blocks = "\n\n".join(
        f"<{key}>\n{value}\n</{key}>"
        for key, value in context.items()
    )

    prompt = f"{blocks}\n\n{step.instruction.format(**params)}"

    return llm(prompt, SYSTEM_PROMPT)


def run_pipeline(
    task: str,
    audience: str = "a general reader",
    max_words: int = 200,
    llm=None
) -> dict:

    # Allows tests to provide their own fake LLM.
    llm = llm or llm_call

    params = {
        "audience": audience,
        "max_words": max_words
    }

    # Start with only the user's request.
    context = {
        "request": task
    }

    # -------------------------
    # Step 1: DRAFT
    # -------------------------
    raw = _run_step(
        DRAFT,
        context,
        params,
        llm
    )

    draft = (
        extract_xml(raw, "draft").strip()
        or raw.strip()
    )

    # Save draft so the next step can see it.
    context["draft"] = draft


    # -------------------------
    # Step 2: CRITIQUE
    # -------------------------
    raw = _run_step(
        CRITIQUE,
        context,
        params,
        llm
    )

    critique = (
        extract_xml(raw, "critique").strip()
        or raw.strip()
    )

    verdict = extract_xml(
        raw,
        "verdict"
    ).strip().lower()

    # Save critique for the final polish step.
    context["critique"] = critique


    # -------------------------
    # Gate: Should we polish?
    # -------------------------
    # This is normal Python logic, not an LLM decision.
    if verdict == "pass":
        return asdict(
            PipelineResult(
                draft,       # final answer
                draft,
                critique,
                verdict,
                steps_run=2
            )
        )


    # -------------------------
    # Step 3: POLISH
    # -------------------------
    raw = _run_step(
        POLISH,
        context,
        params,
        llm
    )

    final = (
        extract_xml(raw, "final").strip()
        or raw.strip()
    )

    return asdict(
        PipelineResult(
            final,
            draft,
            critique,
            verdict or "revise",
            steps_run=3
        )
    )