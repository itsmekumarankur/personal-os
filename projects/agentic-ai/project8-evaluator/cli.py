"""Run the writer and reviewer from the terminal and watch each round.

    python cli.py samples/incident.md
    python cli.py samples/incident.md --max-words 100 --max-rounds 4
"""
import argparse
from pathlib import Path

from refine import refine

parser = argparse.ArgumentParser()
parser.add_argument("file")
parser.add_argument("--max-words", type=int, default=150)
parser.add_argument("--max-rounds", type=int, default=3)
args = parser.parse_args()

r = refine(Path(args.file).read_text(encoding="utf-8"), None, args.max_words, args.max_rounds)

for h in r["history"]:
    print(f"--- round {h['round']}: {h['verdict']} ({h['words']} words, checked by {h['checked_by']}) ---")
    print(h["text"])
    print(f"FEEDBACK: {h['feedback']}\n")

print(f"STATUS: {r['status']}   rounds: {r['rounds']}   model calls: {r['llm_calls']}")
print("\n=== FINAL TEXT ===")
print(r["final"])
