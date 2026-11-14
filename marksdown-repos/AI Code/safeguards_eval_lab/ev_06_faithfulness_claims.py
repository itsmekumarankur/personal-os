"""EV-06  Faithfulness (groundedness), the QAG way: split the answer into claims, verify EACH claim against the context.
Needs a model. Run: python ev_06_faithfulness_claims.py"""
from typing import Literal
from pydantic import BaseModel, Field
from common import get_judge_llm
from eval_data import CORPUS, SYSTEM_A, SYSTEM_B


class Claims(BaseModel):
    claims: list[str] = Field(description="Each distinct factual claim in the answer, as a short standalone sentence")


class ClaimCheck(BaseModel):
    verdict: Literal["supported", "contradicted", "not_enough_info"]
    evidence: str = Field(description="Quote or paraphrase of the context that decides it, or 'none'")


llm = get_judge_llm()
extract = llm.with_structured_output(Claims)
verify = llm.with_structured_output(ClaimCheck)


def faithfulness(answer: str, context: str):
    claims = extract.invoke(f"List every factual claim made in this answer. Answer: {answer}").claims
    rows = []
    for c in claims:
        v = verify.invoke(
            "Using ONLY the context, is the claim supported, contradicted, or is there not enough information?\n"
            f"Context: {context}\nClaim: {c}"
        )
        rows.append((c, v.verdict))
    supported = sum(v == "supported" for _, v in rows)
    return (supported / len(rows) if rows else 0.0), rows


CASES = [
    ("A wrong number",          SYSTEM_A["q2"],                                                   CORPUS["d2"]),
    ("B invented hours",        SYSTEM_B["q4"],                                                   CORPUS["d4"]),
    ("good + one invented fact", "Employees get 24 paid leave days. Unused leave never expires.",  CORPUS["d1"]),
    ("fully grounded",          SYSTEM_A["q1"],                                                   CORPUS["d1"]),
]
for name, answer, context in CASES:
    score, rows = faithfulness(answer, context)
    print(f"\n[{name}] answer: {answer!r}\n  context: {context!r}")
    for claim, verdict in rows:
        print(f"    {verdict:16} <- {claim}")
    print(f"  FAITHFULNESS = {score:.2f}")

print("""
Faithfulness = supported claims / total claims. It measures whether the answer sticks to the CONTEXT, not whether the
context is true. Unlike the number-matching heuristic in EV-08, it understands paraphrase and catches wrong claims that
reuse source words. It costs 1 + (number of claims) judge calls per answer, so run it on samples or nightly.
Scores: low faithfulness with good retrieval = generator problem (prompt/model). Low retrieval metrics (EV-05) = fix retrieval first.""")
