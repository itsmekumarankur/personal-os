"""SG-14  File-access tools: confine the agent to ONE folder (path traversal + symlink defence).
Run: python sg_14_filesystem_path_guard.py   (No LLM needed.)"""
import tempfile
from pathlib import Path

ROOT = Path(tempfile.mkdtemp(prefix="agent_root_")).resolve()      # the ONLY folder the agent may read
OUTSIDE = Path(tempfile.mkdtemp(prefix="outside_")).resolve()      # a different folder the agent must NOT reach
(ROOT / "docs").mkdir()
(ROOT / "docs" / "readme.txt").write_text("Public readme.")
(ROOT / "docs" / "big.txt").write_text("x" * 50_000)
(ROOT / "docs" / "tool.exe").write_text("binary-ish")
(OUTSIDE / "secret.txt").write_text("TOP SECRET")
symlink_ok = True
try:
    (ROOT / "docs" / "shortcut.txt").symlink_to(OUTSIDE / "secret.txt")   # a link that LOOKS like it is inside ROOT
except (OSError, NotImplementedError):
    symlink_ok = False                                                    # Windows without privileges

ALLOWED_EXT = {".txt", ".md"}
MAX_BYTES = 10_000


def safe_read(requested: str) -> str:
    p = (ROOT / requested).resolve()          # resolve() collapses '..' AND follows symlinks to the real location
    if not p.is_relative_to(ROOT):            # the one check that matters: is the REAL path still inside ROOT?
        return "DENIED: outside the allowed folder"
    if p.suffix.lower() not in ALLOWED_EXT:
        return f"DENIED: extension '{p.suffix}' not allowed"
    if not p.is_file():
        return "NOT FOUND"
    if p.stat().st_size > MAX_BYTES:
        return "DENIED: file too large"
    return "OK: " + p.read_text()[:40]


tests = ["docs/readme.txt", "../../etc/passwd", "docs/../../../../etc/hosts", str(OUTSIDE / "secret.txt"),
         "docs/tool.exe", "docs/big.txt", "docs/missing.txt"]
if symlink_ok:
    tests.insert(3, "docs/shortcut.txt")
for t in tests:
    print(f"{t[:48]:48} -> {safe_read(t)}")

print("\nWhy resolve() first: checking the string for '..' is not enough (encodings, symlinks, absolute paths).")
print("Compare the REAL resolved path with the allowed root. Same idea applies to URLs an agent may fetch (SSRF):")
print("resolve the hostname, then refuse private ranges like 127.0.0.1, 10.x, 169.254.169.254 (cloud metadata).")
