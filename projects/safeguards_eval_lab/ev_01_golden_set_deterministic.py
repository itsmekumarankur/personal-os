"""EV-01  Evaluation starts here: a golden set + deterministic metrics.  No LLM.  Run: python ev_01_golden_set_deterministic.py"""
import re
from eval_data import GOLDEN, SYSTEM_A, SYSTEM_B


def norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def exact_match(pred: str, expected: str) -> bool:
    return norm(pred) == norm(expected)


def contains(pred: str, expected: str) -> bool:
    # pad with spaces so "2" does NOT match inside "24" (a classic evaluation bug: substring false positives)
    return f" {norm(expected)} " in f" {norm(pred)} "


def evaluate(system: dict, name: str):
    print(f"\n=== {name} ===")
    em = ct = 0
    for item in GOLDEN:
        pred = system[item["id"]]
        e, c = exact_match(pred, item["expected"]), contains(pred, item["expected"])
        em += e; ct += c
        print(f"  {item['id']} exact={'Y' if e else '-'} contains={'Y' if c else '-'} | expected={item['expected']!r:20} got={pred!r}")
    n = len(GOLDEN)
    print(f"  exact-match accuracy: {em}/{n} = {em / n:.0%}   contains accuracy: {ct}/{n} = {ct / n:.0%}")
    return ct / n


a, b = evaluate(SYSTEM_A, "System A"), evaluate(SYSTEM_B, "System B")
print(f"\nSystem A {a:.0%} vs System B {b:.0%}  -> A wins.")

print("""
What to notice:
  * Exact match is harsh: A says '24 paid leave days...' (correct) but exact-match scores it as wrong.
  * 'Contains' is fairer, but still blind to meaning: 'Not 24 days' would pass. Deterministic metrics are
    cheap, fast, reproducible - use them wherever the answer is a number, ID, label or short string.
  * For free-text answers you need a judge (EV-03). For retrieval you need rank metrics (EV-05).
  * The dataset matters more than the metric: 6 questions is a demo, real golden sets start at 50-200 and grow
    every time production finds a failure.""")


"""
        GOLDEN TEST SET
     (Questions + correct answers)
                 |
                 v
       +--------------------+
       |     SYSTEM A       |
       |  Produces answers  |
       +--------------------+
                 |
                 v
       +--------------------+
       |  COMPARE ANSWERS   |
       |                    |
       |  Exact match?      |
       |  Contains answer?  |
       +--------------------+
                 |
                 v
       +--------------------+
       |  CALCULATE SCORE   |
       |  e.g. 5/6 = 83%   |
       +--------------------+


       Repeat for SYSTEM B
                 |
                 v
       +--------------------+
       | COMPARE A vs B     |
       | Which scores higher?|
       +--------------------+
                 |
                 v
          EVALUATION REPORT

In simple words: 
- You are learning how to test whether an AI system gives correct answers. 
- You prepare a set of questions with known correct answers (the golden set), then compare the answers from System A and System B against those expected answers. 
- The program calculates scores so you can measure and compare their performance without using another LLM to judge them.

Key takeaway: 
- Evaluation helps you measure AI quality instead of guessing. 
- Exact match checks whether the whole normalized answer matches; contains checks whether the expected text appears as a complete phrase. 
- These metrics are fast and repeatable, but they cannot fully understand meaning—for example, “Not 24 days” could still pass a simple contains check
"""