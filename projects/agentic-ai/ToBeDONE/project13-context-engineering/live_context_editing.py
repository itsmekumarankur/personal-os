"""The same ideas with the real API. NOT RUN here (no key, no network). Parameter names are copied from the context-editing docs
(beta header 'context-management-2025-06-27'); the feature is in beta, so re-read the docs before using it.

Server-side tool-result clearing  == context_manager 'clear_results' (the API does the editing for you):
    trigger          start clearing past this many input tokens         (our Config.trigger * budget)
    keep             how many recent tool uses to keep                   (our keep_results)
    clear_at_least   do not bother unless at least this many tokens go   (our 'batch' idea: make each cache rewrite worth it)
    exclude_tools    never clear these tools' results (e.g. the notes/memory tool)
    clear_tool_inputs  also blank the call arguments                     (our clear_results+inputs)
The response reports context_management.applied_edits (how many uses/tokens were cleared).
"""
import anthropic

client = anthropic.Anthropic()


def step(messages, tools, system):
    return client.beta.messages.create(
        model="claude-sonnet-5-5", max_tokens=2000, system=system, messages=messages, tools=tools,
        betas=["context-management-2025-06-27"],
        context_management={"edits": [{
            "type": "clear_tool_uses_20250919",
            "trigger": {"type": "input_tokens", "value": 50_000},
            "keep": {"type": "tool_uses", "value": 5},
            "clear_at_least": {"type": "input_tokens", "value": 10_000},
            "exclude_tools": ["write_note", "read_notes"],
        }]},
    )


def count(messages, system, tools):
    """Free endpoint (rate limited). Count BEFORE you send; budget decisions should use real counts, not chars/4."""
    return client.messages.count_tokens(model="claude-sonnet-5-5", system=system, messages=messages, tools=tools).input_tokens
