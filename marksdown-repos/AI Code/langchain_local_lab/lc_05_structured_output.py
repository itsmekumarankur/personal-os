"""LC-05  Get a typed Python object back (not text).  Run: python lc_05_structured_output.py"""
from pydantic import BaseModel, Field
from common import get_llm


class Invoice(BaseModel):
    """Details extracted from an invoice email."""
    vendor: str = Field(description="Company that sent the invoice")
    amount: float = Field(description="Total amount as a number")
    currency: str = Field(description="3-letter currency code")
    due_date: str = Field(description="Due date in YYYY-MM-DD")


# with_structured_output makes the model fill THIS schema.
extractor = get_llm().with_structured_output(Invoice)

email = "Hi, Acme Cloud Services here. Your invoice total is Rs. 48,250 and payment is due by 15 Nov 2026."
inv = extractor.invoke(f"Extract the invoice details:\n\n{email}")

print(type(inv).__name__)            # Invoice (a real object)
print(inv)
print("amount * 2 =", inv.amount * 2)   # real float, usable in code

"""
Concept. Instead of parsing text, you hand the model a schema and get a validated Python object back.

New things in this step

Pydantic BaseModel + Field(description=...)
llm.with_structured_output(Schema)
Real typed values you can do maths on
Architecture view. Under the hood the schema is sent as a forced tool call; the library validates the result before returning it.

"""