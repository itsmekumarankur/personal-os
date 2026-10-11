"""SG-07  Output-side PII/secret leak scanning: stop the model from echoing back secrets.  Run: python sg_07_output_leak_scan.py"""
import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sg_01_pii_regex import scan as pii_scan, redact as pii_redact   # same patterns work on output

SECRET_PATTERNS = {
    "AWS_KEY":      re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GENERIC_KEY":  re.compile(r"\b(sk|pk|api)[-_][A-Za-z0-9]{20,}\b", re.IGNORECASE),
    "PRIVATE_KEY":  re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    "BEARER_TOKEN": re.compile(r"\bBearer\s+[A-Za-z0-9\-_.]{20,}\b"),
}


def scan_secrets(text: str) -> dict[str, list[str]]:
    hits = {}
    for label, pattern in SECRET_PATTERNS.items():
        found = pattern.findall(text)
        if found:
            hits[label] = found
    return hits


def output_safe(model_output: str) -> tuple[bool, str]:
    """Returns (is_safe, cleaned_or_original_text). Blocks if secrets found, redacts if only PII found."""
    secrets = scan_secrets(model_output)
    if secrets:
        return False, f"[RESPONSE BLOCKED: leaked secret types detected: {list(secrets.keys())}]"
    if pii_scan(model_output):
        return True, pii_redact(model_output)     # redact, don't block
    return True, model_output


if __name__ == "__main__":
    # Simulate things a careless agent (e.g. one that reads files or DB rows) might echo back
    leaky_outputs = [
        "Sure! The total for order #4521 is Rs. 3,200.",
        "Here is the config you asked about: aws_access_key = AKIAABCDEFGHIJKLMNOP",
        "I found this in the logs: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abcdef",
        "Your registered contact is ankur.k@example.com.",
    ]

    for out in leaky_outputs:
        ok, result = output_safe(out)
        label = "BLOCKED " if not ok else ("REDACTED" if result != out else "ALLOWED ")
        print(f"[{label}] {result}")

    print("\n-> Rule of thumb used here: a leaked SECRET (API key, token) = block the whole response.")
    print("   A leaked PII field = usually redact and continue (the user often already knows their own email).")


"""
           AI MODEL GENERATES RESPONSE
                       |
                       v
          +---------------------------+
          | OUTPUT SAFETY CHECK       |
          | Scan response for leaks   |
          +---------------------------+
                       |
                       v
          +---------------------------+
          | 1. CHECK FOR SECRETS      |
          | API keys, bearer tokens,  |
          | private keys, AWS keys    |
          +---------------------------+
                       |
                +------+------+
                |             |
          SECRET FOUND     NO SECRET
                |             |
                v             v
        +---------------+  +----------------------+
        | BLOCK RESPONSE|  | 2. CHECK FOR PII     |
        | Do not expose |  | Email, phone, etc.   |
        | the secret    |  +----------------------+
        +---------------+             |
                               +------+------+
                               |             |
                            PII FOUND     NO PII
                               |             |
                               v             v
                      +----------------+  +----------------+
                      | REDACT PII     |  | ALLOW RESPONSE |
                      | Replace with   |  | As generated   |
                      | masked value   |  +----------------+
                      +----------------+
                               |
                               v
                       SHOW CLEANED RESPONSE
                       TO THE USER
"""