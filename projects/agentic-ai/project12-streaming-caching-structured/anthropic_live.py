"""The same ideas against the REAL Anthropic API. NOT RUN in this project (no key, no network). Read it next to fake_model.py.

pip install anthropic     (the code below follows the SDK's documented interfaces: messages.stream, messages.create, cache_control, tool_choice)
Set ANTHROPIC_API_KEY. Use a model name that exists for your account. Minimum cacheable prompt size depends on the model (512..4096 tokens).
"""
import os

import anthropic

MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")


def stream_text(system_text: str, user_text: str, cache: bool = True):
    """Yield text as it arrives; the final usage shows cache_creation_input_tokens / cache_read_input_tokens."""
    client = anthropic.Anthropic()
    system = [{"type": "text", "text": system_text, **({"cache_control": {"type": "ephemeral"}} if cache else {})}]
    with client.messages.stream(model=MODEL, max_tokens=500, system=system, messages=[{"role": "user", "content": user_text}]) as s:
        yield from s.text_stream
        final = s.get_final_message()
        print("\nusage:", final.usage)


def raw_events(system_text: str, user_text: str):
    """Low-level events (message_start, content_block_delta ...) exactly like events.py expects. Use this to feed StreamAccumulator."""
    client = anthropic.Anthropic()
    stream = client.messages.create(model=MODEL, max_tokens=300, system=system_text, messages=[{"role": "user", "content": user_text}], stream=True)
    for ev in stream:
        yield ev.model_dump()


def extract_invoice(text: str):
    """Forced tool call = layer 1 of structured.py. Validate the result with structured.schema_errors / semantic_errors."""
    import structured
    client = anthropic.Anthropic()
    req = structured.request_for(text)
    req["model"] = MODEL
    req.pop("stream", None)
    msg = client.messages.create(**req)
    tool = next(b for b in msg.content if b.type == "tool_use")
    return tool.input, msg.usage
