"""Run the chain from the terminal and see every step.

    python cli.py "Explain what a load balancer does" --audience "new engineers"
"""
import argparse

from chain import run_pipeline

parser = argparse.ArgumentParser()
parser.add_argument("task")
parser.add_argument("--audience", default="a general reader")
parser.add_argument("--max-words", type=int, default=200)
args = parser.parse_args()

result = run_pipeline(args.task, args.audience, args.max_words)

print("=== DRAFT ===\n" + result["draft"])
print("\n=== CRITIQUE ===\n" + result["critique"])
print(f"\n=== VERDICT: {result['verdict']} (steps run: {result['steps_run']}) ===")
print("\n=== FINAL ===\n" + result["final"])
