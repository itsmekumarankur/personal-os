"""LIVE coding agent: the real Anthropic API drives the same ToolRunner + sandbox. NOT RUN in the session that produced this project
(no API key there). It is a skeleton to read and adapt.

The only difference from the fake model: `model` below is a real API call. Everything else (path jail, protected tests, sandbox,
brakes, independent final check, patch) is unchanged, which is the point: the SAFETY lives in the harness, not in the model.

Anthropic also ships a trained text-editor tool and a bash tool (check the current docs for exact type names and versions; I could not
fetch them when writing this). The custom tools in tools.py have the same shape on purpose: view / create / str_replace / insert.
Run:  ANTHROPIC_API_KEY=... python live_coder.py slugify
"""
import sys

import anthropic

from job import run_job
from sandbox import Limits, LocalProcessSandbox, NamespaceSandbox

MODEL = "claude-sonnet-4-5"          # placeholder: use a current model id from the docs


def make_model(client: anthropic.Anthropic):
    def model(system, messages, tools):
        resp = client.messages.create(model=MODEL, max_tokens=2048, system=system, tools=tools, messages=messages)
        out = []
        for b in resp.content:
            if b.type == "text":
                out.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
        return out
    return model


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "slugify"
    sb = NamespaceSandbox(Limits()) if NamespaceSandbox.available() else LocalProcessSandbox(Limits())
    print("sandbox:", sb.level)
    r = run_job(task, make_model(anthropic.Anthropic()), sb, max_steps=25)
    print(r.outcome.status, "|", r.outcome.stop_reason)
    print(r.outcome.patch)
