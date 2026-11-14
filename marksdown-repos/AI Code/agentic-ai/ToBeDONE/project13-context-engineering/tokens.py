"""A rough token counter (4 characters ~ 1 token). Good enough to SEE the effects; for real bills use the API's usage numbers
(or the count_tokens endpoint). Everything in this project that says 'tokens' uses this one function, so it is easy to swap."""
import json


def count_text(s: str) -> int:
    return max(1, (len(s) + 3) // 4) if s else 0


def count_json(obj) -> int:
    return count_text(json.dumps(obj, sort_keys=True, separators=(",", ":")))
