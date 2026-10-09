"""EXPERIMENT 4 — the file tools are an attack surface too, and error messages are the model's teacher.
Run: python experiments/exp4_tools_and_limits.py"""
import os
import shutil
import tempfile

from _common import table

from sandbox import LocalProcessSandbox, NamespaceSandbox
from tools import ToolRunner
from workspace import Workspace

d = tempfile.mkdtemp()
os.chmod(d, 0o755)
shutil.copytree(os.path.join(os.path.dirname(__file__), "..", "tasks", "median"), d, dirs_exist_ok=True)
open(os.path.join(d, "dup.py"), "w").write("x = 1\nx = 1\n")
sb = NamespaceSandbox() if NamespaceSandbox.available() else LocalProcessSandbox()
ws = Workspace(d)
tr = ToolRunner(ws, sb)

cases = [
    ("str_replace, text not found", "str_replace", {"path": "stats.py", "old_str": "return nothing", "new_str": "x"}),
    ("str_replace, ambiguous (2 matches)", "str_replace", {"path": "dup.py", "old_str": "x = 1", "new_str": "x = 2"}),
    ("path traversal", "view", {"path": "../../etc/passwd"}),
    ("absolute path", "view", {"path": "/etc/passwd"}),
    ("edit a test (reward hacking)", "str_replace", {"path": "tests/test_stats.py", "old_str": "2.5", "new_str": "2"}),
    ("create over an existing file", "create", {"path": "stats.py", "file_text": "x"}),
    ("huge file", "create", {"path": "big.py", "file_text": "x" * 200_000}),
    ("missing argument", "str_replace", {"path": "stats.py"}),
]
rows = [(label, tr.execute(tool, args)[0][:90].replace("\n", " ")) for label, tool, args in cases]
table(rows, ["attempt", "what the model is told"])

print("\n== symlink escape: sandboxed code plants a link, then the agent's tool follows it ==")
open(os.path.join(d, "plant.py"), "w").write("import os\nos.symlink('/etc/hostname', 'link.txt')\nprint('planted')\n")
print("run:", tr.execute("run_python", {"path": "plant.py"})[0].splitlines()[-1])
print("view link.txt ->", tr.execute("view", {"path": "link.txt"})[0])

print("\n== tests rewritten by EXECUTED code are detected and restored ==")
open(os.path.join(d, "hack.py"), "w").write("open('tests/test_stats.py', 'w').write('import unittest\\n')\nprint('rewrote tests')\n")
print("run:", tr.execute("run_python", {"path": "hack.py"})[0].splitlines()[-1])
print("tampered now:", ws.tampered())
print("run_tests says:", tr.execute("run_tests", {})[0].splitlines()[-1][:120])
print("tampered after:", ws.tampered())

print("\n== long output keeps the END ==")
open(os.path.join(d, "noisy.py"), "w").write("for i in range(2000):\n    print('line', i)\nraise SystemExit('FINAL ERROR LINE')\n")
out = tr.execute("run_python", {"path": "noisy.py"})[0]
print(f"{len(out)} chars returned to the model; contains the last line: {'FINAL ERROR LINE' in out}; omitted marker: {'omitted' in out}")
shutil.rmtree(d, ignore_errors=True)
