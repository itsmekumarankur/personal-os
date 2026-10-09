"""Small statistics helpers, written out so you can read the formulas."""
import random
from math import comb


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def percentile(xs, p):
    """Linear interpolation, p in 0..100."""
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def sign_test_p(improved: int, regressed: int) -> float:
    """Two-sided exact sign test. Only cases that CHANGED count (ties carry no information).
    Question it answers: if the change did nothing, how likely is a split this lopsided?
    8 better vs 2 worse -> p = 0.109, which is NOT convincing with only 10 changed cases."""
    n = improved + regressed
    if n == 0:
        return 1.0
    k = min(improved, regressed)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def bootstrap_ci(deltas, iters=2000, seed=0, alpha=0.05):
    """Resample the per-case differences with replacement to see how much the average could wobble."""
    if not deltas:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(deltas)
    means = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n for _ in range(iters))
    return (means[int(iters * alpha / 2)], means[int(iters * (1 - alpha / 2)) - 1])


def cohens_kappa(tp, fp, tn, fn) -> float:
    """Agreement between two raters, corrected for the agreement you would get by luck."""
    n = tp + fp + tn + fn
    if n == 0:
        return 0.0
    po = (tp + tn) / n
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n ** 2
    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)
