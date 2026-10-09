"""EXPERIMENT 1 — twelve hostile (or just buggy) programs, three kinds of sandbox.
Run (needs root + Linux namespaces for L1):  python experiments/exp1_attacks.py"""
from _common import table

from attacks import ATTACKS, cleanup, make_ctx, run_attack
from sandbox import DockerSandbox, Limits, LocalProcessSandbox, NamespaceSandbox

lim = Limits(wall_s=4, cpu_s=2)
levels = [LocalProcessSandbox(lim)]
if NamespaceSandbox.available():
    levels.append(NamespaceSandbox(lim))
else:
    print("(namespaces unavailable here: need root on Linux. L1 skipped.)\n")
ctx = make_ctx()
rows, score = [], {sb.level: 0 for sb in levels}
for a in ATTACKS:
    cells = []
    for sb in levels:
        ok, ev, r = run_attack(sb, a, ctx)
        score[sb.level] += ok
        cells.append(("contained  " if ok else "ESCAPED !! ") + ev[:46])
    rows.append((a.name, a.what[:40], *cells))
cleanup(ctx)
table(rows, ["attack", "what it does", *[sb.level for sb in levels]])
print("\nscore (contained / %d): %s" % (len(ATTACKS), score))
print("""
Reading the table
* Resource attacks (loop, sleep, memory, output, disk) are stopped by LIMITS and a wall clock. Level 0 already does that.
* Everything about WHERE the code can reach (files, network, other processes, who it runs as) needs ISOLATION, not limits:
  Level 0 runs as the same user on the same machine, so it can read your files, call your network and kill your processes.
* Fork bomb: Level 0 cannot enforce a process limit as root. Level 1 gives each run its own unprivileged uid + a pid namespace.
* Environment secrets: both levels pass NOTHING from the parent's environment (no proxy variables, no API keys).""")
print("\nLevel 2 (Docker) was not run here. The command it would execute:\n  " + " ".join(DockerSandbox(lim).command("/tmp/job", ["python", "main.py"])))
