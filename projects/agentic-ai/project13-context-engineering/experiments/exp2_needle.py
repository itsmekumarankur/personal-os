"""EXPERIMENT 2 — 'does a fact from step N survive until step 101?' for several N, and what happens when the model guesses.
Run: python experiments/exp2_needle.py"""
from _common import table

from agent import run
from fake_model import ContextAgentModel
from world import World

POS = [3, 30, 60, 90, 97]
STRATS = ["window", "clear_results", "summarize_lossy", "summarize_structured", "clear+ledger", "clear+notes"]
rows = []
for s in STRATS:
    cells = []
    for p in POS:
        w = World(code_at=p, region_at=p + 2)
        r = run(s, world=w)
        cells.append("ok" if r.correct else "LOST")
    rows.append((s, *cells))
print("fact planted at shard N (the question is asked after shard 100)\n")
table(rows, ["strategy"] + [f"N={p}" for p in POS])
print("\nRecency hides the problem: a fact planted at shard 97 is still in the newest messages, so every strategy 'works'. Test the OLD facts (the step-3 test).\n")

print("== when the model cannot find the fact: honest 'I don't know' vs confident wrong answer ==")
rows = []
for conf in (False, True):
    m = ContextAgentModel(confabulate=conf)
    r = run("summarize_lossy", model=m, world=World(decoy_at=95))          # a revoked-code decoy sits in the newest shards
    verdict = "correct" if r.correct else ("CONFIDENT AND WRONG" if "cannot find" not in r.answer else "says it cannot find it")
    rows.append(("confabulating" if conf else "honest", r.answer[:70], verdict))
table(rows, ["model", "answer", "verdict"])
print("The confabulating model grabbed the REVOKED code K7-ALPHA-1180 it could still see. In a bank that is a refund approved with a dead code.")
print("A visible-but-wrong lookalike is more dangerous than a missing fact. Defences: tell the model to say 'cannot find' instead of guessing, keep decoys/stale data out of context, and eval for it (Project 15).")
