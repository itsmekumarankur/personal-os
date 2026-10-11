"""One job = one fresh directory + one sandbox run per command + a patch at the end + everything destroyed afterwards.
Nothing from job A can be seen by job B (no shared files, no shared processes, no shared secrets)."""
import os
import shutil
import tempfile
from dataclasses import dataclass

from agent import JobOutcome, run_agent
from audit import AuditLog
from tools import ToolRunner
from workspace import Workspace

HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass
class JobResult:
    outcome: JobOutcome
    audit: AuditLog
    dir_removed: bool
    job_dir: str


def run_job(task: str, model, sandbox, fill: dict | None = None, audit_path: str | None = None, **agent_kw) -> JobResult:
    job_dir = tempfile.mkdtemp(prefix=f"job-{task}-")
    os.chmod(job_dir, 0o755)
    try:
        src = os.path.join(HERE, "tasks", task)
        shutil.copytree(src, job_dir, dirs_exist_ok=True)
        for dp, _, fns in os.walk(job_dir):                              # fill placeholders (used by the injection demo)
            for fn in fns:
                if fn.endswith(".md") and fill:
                    p = os.path.join(dp, fn)
                    t = open(p).read()
                    for k, v in fill.items():
                        t = t.replace("{" + k + "}", str(v))
                    open(p, "w").write(t)
        ws = Workspace(job_dir)
        audit = AuditLog(audit_path, job=os.path.basename(job_dir))
        runner = ToolRunner(ws, sandbox, audit)
        goal = "Read README.md for the task description." if os.path.exists(os.path.join(job_dir, "README.md")) else f"Task: {task}"
        outcome = run_agent(model, runner, "Make the tests in tests/ pass. " + goal, **agent_kw)
    finally:
        shutil.rmtree(job_dir, ignore_errors=True)                       # destroy the workspace
    return JobResult(outcome, audit, not os.path.exists(job_dir), job_dir)
