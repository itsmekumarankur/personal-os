"""
05 OUTPUT GUARDRAILS  -  "what is allowed to LEAVE the agent?"

The model's answer is a draft until it passes checks. Typical checks for a finance assistant:
  1. STRUCTURE   must be valid JSON with required fields (downstream code depends on it)
  2. SECRETS     no API keys / credentials leaked from prompt, tools or memory
  3. PII LEAK    no card numbers or PAN that the user was not meant to see
  4. FORBIDDEN   no promises like "guaranteed returns" (regulatory risk)
  5. GROUNDING   every number in the answer must exist in the retrieved facts  <- stops hallucinated figures
  6. REQUIRED    source citation + risk disclaimer when talking about returns
  7. REPAIR LOOP if a check fails, send the failure reasons back to the model and retry (max N),
                 then fall back to a safe canned answer. Never ship a failed draft.

The "model" below is scripted so the demo is deterministic.
Run: python 05_output_guardrails.py
"""
import json
import re

FACTS = "Fund: HDFC Flexi. NAV 52.30. 1-year return 11.2%. Expense ratio 0.45%."
FACT_NUMBERS = set(re.findall(r"\d+(?:\.\d+)?", FACTS))
FORBIDDEN = ["guaranteed return", "risk-free", "cannot lose", "sure profit"]
SECRET = r"AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|password\s*[:=]"
SAFE_FALLBACK = {"answer": "I could not produce a verified answer. A human advisor will follow up.", "sources": [], "confidence": 0.0}


def validate(raw):
    problems = []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ["not valid JSON"], None
    for key, typ in (("answer", str), ("sources", list), ("confidence", (int, float))):
        if not isinstance(data.get(key), typ):
            problems.append(f"missing/invalid field '{key}'")
    if problems:
        return problems, None
    text = data["answer"]
    if re.search(SECRET, text):
        problems.append("secret/credential leaked")
    if re.search(r"\b(?:\d[ -]?){15}\d\b", text):
        problems.append("card number in output")
    for phrase in FORBIDDEN:
        if phrase in text.lower():
            problems.append(f"forbidden claim: '{phrase}'")
    for num in re.findall(r"\d+(?:\.\d+)?", text):
        if num not in FACT_NUMBERS:
            problems.append(f"ungrounded number {num} (not in retrieved facts)")
    if not data["sources"]:
        problems.append("no sources cited")
    if re.search(r"return|nav|fund", text, re.I) and "past performance" not in text.lower():
        problems.append("missing risk disclaimer")
    if not 0 <= data["confidence"] <= 1:
        problems.append("confidence outside 0..1")
    return problems, data


def guarded_answer(model, max_retries=2):
    feedback = None
    for attempt in range(1, max_retries + 2):
        raw = model(attempt, feedback)
        problems, data = validate(raw)
        print(f"   attempt {attempt}: " + ("PASS" if not problems else f"FAIL {problems}"))
        if not problems:
            return data
        feedback = problems                      # real systems append this to the next prompt
    print("   retries exhausted -> safe fallback")
    return SAFE_FALLBACK


def j(**kw):
    return json.dumps(kw)


GOOD = j(answer="HDFC Flexi has NAV 52.30 and a 1-year return of 11.2%. Past performance is not indicative of future returns.",
         sources=["factsheet"], confidence=0.9)
SCENARIOS = {
    "first draft is bad, second is fixed (repair loop works)": lambda a, fb: [
        j(answer="HDFC Flexi NAV is 61.00 with guaranteed returns of 20%. key=AKIAABCDEFGHIJKLMNOP", sources=[], confidence=0.99),
        GOOD][a - 1],
    "model returns prose instead of JSON, then complies": lambda a, fb: ["Sure! The fund looks great.", GOOD][a - 1],
    "model never behaves (fallback used)": lambda a, fb: j(answer="Risk-free 30% profit, NAV 99", sources=[], confidence=1),
    "clean answer on the first try": lambda a, fb: GOOD,
}

if __name__ == "__main__":
    for name, model in SCENARIOS.items():
        print(f"\n>> {name}")
        result = guarded_answer(model)
        print(f"   DELIVERED: {result['answer']}")
