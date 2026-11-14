"""EV-09  Consistency: ask the SAME question several times. Unstable answers are a risk signal; majority vote can improve accuracy.
Needs a model. Run: python ev_09_consistency_self_consistency.py"""
import re
from collections import Counter
from common import get_llm

llm = get_llm()
N = 6

# Part 1: a question with ONE right answer. Measure agreement AND accuracy (they are different things).
Q1 = ("A bat and a ball cost Rs. 110 together. The bat costs Rs. 100 more than the ball. "
      "How much does the ball cost in rupees? Reply with just the number.")
EXPECTED = "5"


def first_number(text: str) -> str:
    m = re.search(r"\d+(?:\.\d+)?", text)
    return m.group(0) if m else "none"


answers = [first_number(llm.invoke(Q1).text) for _ in range(N)]
counts = Counter(answers)
majority, votes = counts.most_common(1)[0]
print("--- Part 1: numeric question, asked", N, "times ---")
print("answers:", answers)
print(f"agreement (share of the most common answer): {votes / N:.0%}")
print(f"accuracy of each run: {sum(a == EXPECTED for a in answers) / N:.0%}    majority-vote answer: {majority} ({'correct' if majority == EXPECTED else 'WRONG'})")

# Part 2: open-ended question. Count distinct answers as a rough stability signal.
Q2 = "Name the single biggest risk of giving an AI agent write access to a production database. Answer in at most 6 words."
free = [re.sub(r"[^a-z ]", "", llm.invoke(Q2).text.lower()).strip() for _ in range(N)]
print("\n--- Part 2: open-ended question, asked", N, "times ---")
for f in free:
    print("  -", f)
print(f"distinct answers: {len(set(free))} of {N}  (more distinct = less stable; judge with EV-03 to see if they still mean the same thing)")

print("""
Take-aways:
  * Consistency is NOT correctness: a model can be consistently wrong. Always pair it with an accuracy metric.
  * Low agreement on a factual question is a red flag: the model is guessing. Route those cases to retrieval, a tool, or a human.
  * Self-consistency: ask N times, take the majority answer. It often raises accuracy on reasoning tasks, at N times the cost.
  * Randomness comes from sampling; lower temperature reduces it but does not remove it.""")
