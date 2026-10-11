"""Checks before the model sees the text, and before the customer sees the answer.

These are cheap rules in code. They catch common problems and are one layer among several
(authorization in tools.py matters more). They are not a complete defence: new attacks need new rules.
"""
import re

INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"ignore\s+(?:all\s+|any\s+|the\s+|your\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|rules|prompts?)",
    r"disregard\s+(?:your|the|all)\s+(?:instructions|rules|system\s+prompt)",
    r"(?:reveal|show|print|repeat|tell\s+me)\s+(?:me\s+)?(?:your|the)\s+(?:system\s+prompt|hidden\s+instructions)",
    r"you\s+are\s+now\s+(?:dan|an?\s+unrestricted|in\s+developer\s+mode)",
    r"developer\s+mode",
    r"act\s+as\s+.{0,40}without\s+(?:any\s+)?(?:restrictions|rules|limits)",
]]

CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
AADHAAR_RE = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
SECRET_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")
ACCOUNT_RE = re.compile(r"\bA-\d{4}\b")


def luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def redact(text: str) -> tuple[str, list[str]]:
    """Replace card numbers (Luhn-valid), PAN, Aadhaar-like numbers and API-key-like strings."""
    kinds: list[str] = []

    def card(m):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            kinds.append("card_number")
            return "[REDACTED_CARD]"
        return m.group(0)

    text = CARD_RE.sub(card, text)
    for name, pattern, label in [("pan", PAN_RE, "[REDACTED_ID]"), ("aadhaar", AADHAAR_RE, "[REDACTED_ID]"),
                                 ("secret", SECRET_RE, "[REDACTED_SECRET]")]:
        text, n = pattern.subn(label, text)
        if n:
            kinds.append(name)
    return text, sorted(set(kinds))


def looks_like_injection(text: str) -> bool:
    return any(p.search(text) for p in INJECTION_PATTERNS)


def check_output(text: str, own_account_id: str | None) -> tuple[str, list[str]]:
    """Clean the model's answer: no card numbers or secrets, and no account id other than the caller's."""
    text, kinds = redact(text)
    foreign = [a for a in set(ACCOUNT_RE.findall(text)) if a != own_account_id]
    for a in foreign:
        text = text.replace(a, "[REDACTED_ACCOUNT]")
    if foreign:
        kinds.append("foreign_account")
    return text[:4000], sorted(set(kinds))
