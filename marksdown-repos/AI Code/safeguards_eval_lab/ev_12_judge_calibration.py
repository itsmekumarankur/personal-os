"""EV-12  Can you trust your LLM judge? Compare it with human labels: agreement, Cohen's kappa, leniency.
No LLM (recorded labels). Run: python ev_12_judge_calibration.py"""

# 1 = acceptable answer, 0 = not acceptable. Humans labelled 12 answers; the judge model labelled the same 12 (see EV-03).
HUMAN = [1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1]
JUDGE = [1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1]      # this judge is too lenient: it passes things humans rejected


def confusion(h, j):
    tp = sum(a == 1 and b == 1 for a, b in zip(h, j)); tn = sum(a == 0 and b == 0 for a, b in zip(h, j))
    fp = sum(a == 0 and b == 1 for a, b in zip(h, j)); fn = sum(a == 1 and b == 0 for a, b in zip(h, j))
    return tp, fp, fn, tn


def cohens_kappa(h, j):
    n = len(h)
    po = sum(a == b for a, b in zip(h, j)) / n                                   # observed agreement
    pe = sum((h.count(c) / n) * (j.count(c) / n) for c in (0, 1))                # agreement expected by pure chance
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


tp, fp, fn, tn = confusion(HUMAN, JUDGE)
n = len(HUMAN)
agree = (tp + tn) / n
kappa = cohens_kappa(HUMAN, JUDGE)

print(f"items: {n}")
print(f"                judge PASS | judge FAIL")
print(f"  human PASS        {tp:3}    |    {fn:3}")
print(f"  human FAIL        {fp:3}    |    {tn:3}   <- judge passed {fp} answers humans rejected")
print(f"\nraw agreement : {agree:.0%}")
print(f"Cohen's kappa : {kappa:.2f}   (agreement beyond chance; 0 = chance, 1 = perfect)")
print(f"human pass-rate {sum(HUMAN) / n:.0%} vs judge pass-rate {sum(JUDGE) / n:.0%}  -> judge is {'LENIENT' if sum(JUDGE) > sum(HUMAN) else 'harsh or fair'}")

if kappa >= 0.8:   verdict = "excellent: judge can replace most human review"
elif kappa >= 0.6: verdict = "acceptable: use it, spot-check regularly"
else:              verdict = "NOT TRUSTWORTHY: fix the rubric/judge prompt or use a stronger judge before relying on it"
print("verdict:", verdict)

print("""
Why this matters: an LLM judge is itself a model that can be biased. Common judge problems:
  * leniency / self-preference (rates answers from its own model family higher)
  * position bias (prefers the first option in pairwise tests, see EV-04)
  * verbosity bias (longer answers score higher)
Calibration routine: (1) have a human label 30-100 examples, (2) run the judge on the same examples (EV-03),
(3) compute agreement + kappa here, (4) tweak rubric / examples / judge model, repeat, (5) re-check whenever you
change the judge model. Keep the human-labelled set as a permanent regression test FOR THE JUDGE.""")
