import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
RAMP = " .:-=+*#%@"


def table(rows, header):
    w = [max(len(str(x)) for x in col) for col in zip(header, *rows)]
    print("  ".join(h.ljust(n) for h, n in zip(header, w)))
    print("  ".join("-" * n for n in w))
    for r in rows:
        print("  ".join(str(x).ljust(n) for x, n in zip(r, w)))


def spark(values, top, width=60):
    """ASCII bar-per-column of tokens over steps. '@' = at the budget."""
    if not values:
        return ""
    cols = []
    for i in range(width):
        a, b = int(i * len(values) / width), max(int((i + 1) * len(values) / width), int(i * len(values) / width) + 1)
        v = max(values[a:b])
        cols.append(RAMP[min(len(RAMP) - 1, int(v / top * (len(RAMP) - 1) + 0.5))])
    return "".join(cols)
