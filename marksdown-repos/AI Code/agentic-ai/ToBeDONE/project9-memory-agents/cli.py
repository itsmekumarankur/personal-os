"""Chat from the terminal and watch the memory grow.

    python cli.py --user ankur                    chat (type 'exit' to stop)
    python cli.py --user ankur --session s2       a new conversation; memory is kept
    python cli.py --user ankur --show             print what is remembered
    python cli.py --user ankur --forget           delete everything about this user

Memory is stored in ./data/memory (change with MEMORY_DIR). Needs ANTHROPIC_API_KEY for chat.
"""
import argparse
import os

from agents import SessionStore, chat_turn, remember
from memory_store import MemoryStore

parser = argparse.ArgumentParser()
parser.add_argument("--user", required=True)
parser.add_argument("--session", default="cli")
parser.add_argument("--show", action="store_true")
parser.add_argument("--forget", action="store_true")
args = parser.parse_args()

store = MemoryStore(os.environ.get("MEMORY_DIR", "./data/memory"))
mem = store.user(args.user)

if args.show:
    files = mem.files()
    for path, text in files.items():
        print(f"=== {path} ===\n{text}")
    print("(nothing remembered yet)" if not files else "")
elif args.forget:
    mem.clear()
    print("forgotten")
else:
    sessions = SessionStore()
    while True:
        try:
            message = input("you> ").strip()
        except EOFError:
            break
        if message in ("exit", "quit"):
            break
        if not message:
            continue
        result = chat_turn(store, sessions, args.user, args.session, message)
        print(f"assistant> {result['reply']}\n   [agents: {', '.join(result['agents_used'])}; "
              f"model calls: {result['usage']['calls']}]")
        saved = remember(store, args.user, message, result["reply"])
        if saved["changes"]:
            print(f"   [memory: {'; '.join(saved['changes'])}]")
