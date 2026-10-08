"""Try both patterns from the terminal.

    python cli.py review samples/design.md
    python cli.py review samples/design.md --reviewers security cost
    python cli.py vote samples/design.md "Is there a credential stored in the repository?" --votes 5
"""
import argparse
from pathlib import Path

from review import review_design
from vote import vote

parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="command", required=True)

p_review = sub.add_parser("review")
p_review.add_argument("file")
p_review.add_argument("--reviewers", nargs="*")

p_vote = sub.add_parser("vote")
p_vote.add_argument("file")
p_vote.add_argument("question")
p_vote.add_argument("--votes", type=int, default=5)

args = parser.parse_args()
text = Path(args.file).read_text(encoding="utf-8")

if args.command == "review":
    r = review_design(text, args.reviewers)
    for rev in r["reviews"]:
        print(f"--- {rev['reviewer']}: {rev['verdict'] or 'FAILED'} ({rev['high_count']} high) ---")
        print(rev["findings"] or rev["error"])
    print("\n=== SUMMARY ===")
    print(r["summary"])
    t = r["timing"]
    print(f"\nVERDICT: {r['verdict']}   complete: {r['complete']}")
    print(f"Reviewers ran in {t['review_wall_seconds']}s; run one after another they would take about "
          f"{t['review_sum_seconds']}s.")
else:
    print(vote(text, args.question, args.votes))
