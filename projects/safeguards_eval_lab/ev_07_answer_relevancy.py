"""EV-07  Answer relevancy: does the answer actually address the question? (sentence-level judge).
Needs a model. Run: python ev_07_answer_relevancy.py"""
import re
from pydantic import BaseModel, Field
from common import get_judge_llm


class SentenceCheck(BaseModel):
    relevant: bool = Field(description="True if the sentence helps answer the question")
    reason: str = Field(description="Max 10 words")


judge = get_judge_llm().with_structured_output(SentenceCheck)


def relevancy(question: str, answer: str):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if s.strip()]
    rows = []
    for s in sentences:
        r = judge.invoke(f"Question: {question}\nDoes this sentence help answer the question?\nSentence: {s}")
        rows.append((s, r.relevant))
    return sum(r for _, r in rows) / len(rows), rows


CASES = [
    ("focused",       "How many paid leave days per year?", "Employees get 24 paid leave days per year."),
    ("padded",        "How many paid leave days per year?", "Employees get 24 paid leave days per year. Our company was founded in 1998. Chennai is a coastal city."),
    ("dodges",        "How many paid leave days per year?", "Leave is an important part of a healthy work culture. Many companies value it."),
    ("wrong but on-topic", "How many days can I work from home?", "You can work from home 3 days per week."),
]
for name, q, a in CASES:
    score, rows = relevancy(q, a)
    print(f"\n[{name}] Q: {q}")
    for s, ok in rows:
        print(f"   {'relevant  ' if ok else 'IRRELEVANT'} | {s}")
    print(f"   RELEVANCY = {score:.2f}")

print("""
Relevancy is NOT correctness: the last case is perfectly on-topic and still wrong ('3 days' vs 2). That is why you
track several metrics together:
   relevancy (on topic?)  +  faithfulness (EV-06, grounded?)  +  correctness (EV-01/03, matches the truth?)
Typical diagnosis: high relevancy + low faithfulness = confident invention; low relevancy = prompt/format problem.""")
