"""Route a ticket from the terminal, or run the built-in samples.

    python cli.py "I was charged twice for my subscription this month"
    python cli.py --samples
"""
import argparse

from router import route_ticket

SAMPLES = [
    "I can't log in. It says 'invalid password' and I need access before end of day.",
    "I was charged $49.99 but I expected the $29.99 plan. Why the difference?",
    "My export to Excel keeps failing with error 500 when the project has over 10,000 rows.",
    "What does the 'workspace templates' feature do and how do I use it?",
    "Fix this now or my lawyer will be contacting you about the data leak.",
]

parser = argparse.ArgumentParser()
parser.add_argument("ticket", nargs="?")
parser.add_argument("--samples", action="store_true", help="run the built-in sample tickets")
args = parser.parse_args()

tickets = SAMPLES if args.samples else [args.ticket] if args.ticket else []
if not tickets:
    parser.error("give a ticket or use --samples")

for t in tickets:
    result = route_ticket(t)
    print("=" * 70)
    print("TICKET:", t)
    print(f"ROUTE: {result['route']}   escalated: {result['escalated']}")
    print("WHY:", result["reasoning"])
    print("-" * 70)
    print(result["reply"])
