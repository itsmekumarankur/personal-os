"""STATE + REDUCERS.

A graph's state is a dict. Nodes do not mutate it; they RETURN an update (a partial dict). The framework merges the update into the state
with a per-key REDUCER. This is the single most important idea in graph frameworks, because of parallel nodes:

    two nodes both return {"notes": ["x"]} and {"notes": ["y"]} in the same step.
    overwrite reducer -> one of them silently WINS and the other is lost (and which one depends on ordering)
    append reducer    -> both survive, order-independent

If you remember one thing: "what happens when two branches write the same key?" must have an answer by design.
"""


def overwrite(old, new):
    return new


def append(old, new):
    return list(old or []) + (list(new) if isinstance(new, (list, tuple)) else [new])


def merge(old, new):
    return {**(old or {}), **new}


def apply_update(state: dict, update: dict, reducers: dict) -> dict:
    """Pure function: returns a NEW state (the old one stays valid, which is what makes checkpoints and time travel possible)."""
    out = dict(state)
    for k, v in (update or {}).items():
        out[k] = reducers.get(k, overwrite)(out.get(k), v)
    return out
