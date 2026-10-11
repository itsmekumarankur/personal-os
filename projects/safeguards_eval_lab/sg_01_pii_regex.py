"""SG-01  PII detection with regex: the cheapest, fastest safeguard.  Run: python sg_01_pii_regex.py"""
import re

# Each pattern: (label, compiled regex). Order matters only for overlapping matches.
PII_PATTERNS = {
    "EMAIL":      re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "PHONE_IN":   re.compile(r"\b[6-9]\d{9}\b"),                      # 10-digit Indian mobile
    "CARD":       re.compile(r"\b(?:\d[ -]?){13,16}\b"),              # 13-16 digits, spaced or dashed
    "AADHAAR":    re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "IFSC":       re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
    "AWS_KEY":    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def scan(text: str) -> dict[str, list[str]]:
    """Return {label: [matches]} for every PII pattern found."""
    hits = {}
    for label, pattern in PII_PATTERNS.items():
        found = pattern.findall(text)
        if found:
            hits[label] = found
    return hits


def redact(text: str) -> str:
    """Replace every match with a [LABEL_REDACTED] placeholder."""
    out = text
    for label, pattern in PII_PATTERNS.items():
        out = pattern.sub(f"[{label}_REDACTED]", out)
    return out


if __name__ == "__main__":
    sample = (
        "Hi, I'm Ankur. My email is ankur.k@example.com and my phone is 9876543210. "
        "Please refund to card 4111 1111 1111 1111, IFSC code HDFC0001234. "
        "Also here is my AWS key AKIAABCDEFGHIJKLMNOP by mistake."
    )

    print("--- scan() finds what is there, without changing anything ---")
    for label, matches in scan(sample).items():
        print(f"  {label:10} -> {matches}")

    print("\n--- redact() is what you actually send onward (to the LLM, to logs) ---")
    print(redact(sample))

    print("\n--- why regex alone is not enough ---")
    tricky = "My number is 98765 43210 and my mail is ankur dot k at example dot com"
    print("scan on obfuscated text:", scan(tricky))
    print("-> spaced-out numbers and 'dot/at' spelled out slip through. See SG-02 for a second layer.")


"""
           USER'S MESSAGE
                  |
                  v
       +----------------------+
       |     REGEX SCANNER    |
       | Looks for patterns   |
       |                      |
       | Email                |
       | Indian mobile number |
       | Credit card number   |
       | Aadhaar number        |
       | IFSC code             |
       | AWS access key        |
       +----------------------+
                  |
                  v
       +----------------------+
       |   PII DETECTED?      |
       +----------------------+
                  |
                  v
       +----------------------+
       |    redact()          |
       | Replaces sensitive   |
       | values with labels   |
       +----------------------+
                  |
                  v
       "My email is [EMAIL_REDACTED]
        and phone is [PHONE_IN_REDACTED]"
                  |
                  v
       SEND CLEANED TEXT TO LLM
       OR STORE IN LOGS

In simple words: 
    You are learning how to protect sensitive information before sending a user's message to an AI model or saving it in logs. The program uses regular expressions (regex) to detect patterns such as email addresses, mobile numbers, card numbers, Aadhaar numbers, IFSC codes, and AWS access keys. It then replaces detected values with labels such as [EMAIL_REDACTED], so the original values are not passed downstream.
Key takeaway: 
    This is a fast, inexpensive first layer of AI safety called PII detection and redaction. However, regex only catches patterns it recognizes. For example, a phone number written with unusual spacing or an email written as “ankur dot k at example dot com” may escape detection. Production systems need additional safeguards and testing; this demo's patterns are not comprehensive validators of the underlying identifiers.
"""