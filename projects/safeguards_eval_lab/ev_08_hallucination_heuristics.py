"""EV-08  Cheap hallucination detection WITHOUT a judge: are the answer's numbers and names found in the source?
No LLM. Run: python ev_08_hallucination_heuristics.py"""
import re
from eval_data import GOLDEN, CORPUS, SYSTEM_A, SYSTEM_B

STOPCAPS = {"The", "You", "Employees", "Insurance", "Up", "Within", "I", "Travel", "Claims", "A", "An"}


def facts_in(text: str) -> set[str]:
    nums = set(re.findall(r"\d+", text))
    caps = {w for w in re.findall(r"\b[A-Z][a-zA-Z]+\b", text) if w not in STOPCAPS}
    return nums | caps


def grounding_check(answer: str, context: str) -> tuple[bool, set[str]]:
    unsupported = facts_in(answer) - facts_in(context)
    return (not unsupported, unsupported)


def run(system: dict, name: str):
    print(f"\n=== {name} ===")
    grounded = 0
    for item in GOLDEN:
        context = " ".join(CORPUS[d] for d in item["relevant_docs"])
        ok, bad = grounding_check(system[item["id"]], context)
        grounded += ok
        print(f"  {item['id']} {'GROUNDED' if ok else 'SUSPECT '} {system[item['id']]!r}" + ("" if ok else f"  <- not in source: {sorted(bad)}"))
    print(f"  grounding rate: {grounded}/{len(GOLDEN)}")


run(SYSTEM_A, "System A"); run(SYSTEM_B, "System B")

print("""
What this catches: invented numbers ('3 days', '60 days', '24x7') and invented names. Fast, free, explainable.
What it misses (so use it as a first filter, not the verdict):
  * wrong claims that reuse source words:  'Monday to Sunday' passes if both days appear elsewhere
  * paraphrase / derived numbers: 'twice a week' vs '2', or 24 + 10 = 34 would be flagged as unsupported (false positive)
  * missing answers: 'I am not sure' is grounded but useless (that is what EV-01 and EV-07 measure)
Next level: claim-by-claim verification with a judge model (EV-06).""")
