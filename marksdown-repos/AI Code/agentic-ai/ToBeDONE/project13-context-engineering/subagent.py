"""Context isolation: give a messy sub-task to a SUB-agent with its own window; keep only its short report.
The sub-agent's whole transcript is thrown away. This protects the PARENT's context. It does not make the work cheaper:
the sub-agent still reads every token (see experiments/exp4_jit_and_subagents.py)."""
from agent import run
from world import World


def delegate(world: World, strategy: str = "clear+ledger") -> tuple:
    """Returns (report_text, result). The report is what the parent sees; result carries the sub-agent's own token bill."""
    res = run(strategy, world=world, ask_final=False)
    report = "Sub-agent report (shards 1..%d scanned):\n%s" % (world.total, "\n".join(res.ledger) or "(no facts found)")
    return report, res
