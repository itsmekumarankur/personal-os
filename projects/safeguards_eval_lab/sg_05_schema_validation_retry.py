"""SG-05  Output schema validation + corrective retry (deterministic, no judge needed).  Run: python sg_05_schema_validation_retry.py"""
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from common import get_llm


class SupportTicket(BaseModel):
    category: Literal["billing", "technical", "account", "other"]      # a closed set, enforced by Pydantic
    priority: Literal["low", "medium", "high"]
    summary: str = Field(description="One sentence summary")


llm = get_llm()

GOOD_PROMPT = (
    "Classify this support message as JSON with keys category, priority, summary. "
    "category must be one of billing/technical/account/other. priority must be low/medium/high.\n\n"
    "Message: My card was charged twice for the same transaction, please help urgently."
)


def classify_with_retry(prompt: str, max_attempts: int = 3) -> SupportTicket:
    """Deterministic safeguard: validate structure, and if invalid, tell the model exactly
    what was wrong and ask again - instead of silently crashing or passing bad data onward."""
    structured = llm.with_structured_output(SupportTicket, include_raw=True)
    last_error = None
    for attempt in range(1, max_attempts + 1):
        result = structured.invoke(prompt if attempt == 1 else f"{prompt}\n\nYour previous attempt was invalid: {last_error}. Fix it.")
        parsed = result.get("parsed")
        if parsed is not None:
            print(f"  attempt {attempt}: OK")
            return parsed
        last_error = str(result.get("parsing_error"))
        print(f"  attempt {attempt}: FAILED validation -> {last_error[:100]}")
    raise ValueError(f"Could not get valid output after {max_attempts} attempts")


print("--- normal case ---")
ticket = classify_with_retry(GOOD_PROMPT)
print(ticket)

print("\n--- manual validation example (what with_structured_output does under the hood) ---")
raw_model_text = '{"category": "billing", "priority": "super-duper-urgent", "summary": "double charge"}'
import json
try:
    SupportTicket.model_validate(json.loads(raw_model_text))
except ValidationError as e:
    print("Pydantic rejects an invalid enum value:")
    print(" ", str(e).splitlines()[0])
    print("  -> this is EXACTLY the kind of bad output that reaches real code and crashes it, if unchecked.")


"""
              SUPPORT MESSAGE
                     |
                     v
       +---------------------------+
       |       LLM CLASSIFIER      |
       |                           |
       | Read the customer's issue |
       | and generate a JSON result|
       +---------------------------+
                     |
                     v
       +---------------------------+
       |    PYDANTIC VALIDATION    |
       |                           |
       | Is category valid?        |
       | Is priority valid?        |
       | Is summary a string?      |
       +---------------------------+
                     |
             +-------+-------+
             |               |
          VALID            INVALID
             |               |
             v               v
       +-------------+  +------------------+
       | Return the  |  | Capture parsing  |
       | valid ticket|  | or validation    |
       |             |  | error             |
       +-------------+  +------------------+
                                |
                                v
                       +------------------+
                       | RETRY THE LLM    |
                       |                  |
                       | Send the original|
                       | prompt plus the  |
                       | validation error |
                       +------------------+
                                |
                                v
                       +------------------+
                       | Try again, up to |
                       | 3 attempts        |
                       +------------------+
                                |
                                v
                       +------------------+
                       | Still invalid?   |
                       | Raise an error   |
                       +------------------+
"""