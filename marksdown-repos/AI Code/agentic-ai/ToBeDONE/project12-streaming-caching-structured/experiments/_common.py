import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def table(rows, header):
    w = [max(len(str(x)) for x in col) for col in zip(header, *rows)]
    line = "  ".join(h.ljust(n) for h, n in zip(header, w))
    print(line)
    print("  ".join("-" * n for n in w))
    for r in rows:
        print("  ".join(str(x).ljust(n) for x, n in zip(r, w)))


def bar(x, scale, ch="#"):
    return ch * max(0, int(round(x / scale)))
