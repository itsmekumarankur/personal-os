import os
import shutil
import tempfile

import pytest
from conftest import LIM, needs_ns

from attacks import cleanup, make_ctx
from audit import risk_flags
from fake_coder import FakeCoder, GullibleCoder
from job import HERE, run_job
from sandbox import LocalProcessSandbox, NamespaceSandbox
from tools import clip, parse_unittest
from workspace import Workspace, WorkspaceError


@pytest.fixture
def ws():
    d = tempfile.mkdtemp()
    os.chmod(d, 0o755)
    shutil.copytree(os.path.join(HERE, "tasks", "median"), d, dirs_exist_ok=True)
    open(os.path.join(d, "dup.py"), "w").write("x = 1\nx = 1\n")
    w = Workspace(d)
    yield w
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- file tools
@pytest.mark.parametrize("bad", ["../x", "/etc/passwd", "a/../../x", "~/x", "", "a\x00b"])
def test_path_jail(ws, bad):
    with pytest.raises(WorkspaceError):
        ws.view(bad)


@pytest.mark.parametrize("bad", ["../x", "/etc/passwd", "a/../../x", "~/x"])
def test_path_jail_explains_itself(ws, bad):
    with pytest.raises(WorkspaceError, match="relative and stay inside"):
        ws.view(bad)


def test_symlink_escape_refused(ws):
    os.symlink("/etc/hostname", os.path.join(ws.root, "link"))
    with pytest.raises(WorkspaceError, match="outside"):
        ws.view("link")


def test_protected_tests_cannot_be_edited_or_created(ws):
    for call in (lambda: ws.str_replace("tests/test_stats.py", "2.5", "2"), lambda: ws.create("tests/new.py", "x"), lambda: ws.insert("tests/test_stats.py", 0, "x")):
        with pytest.raises(WorkspaceError, match="protected"):
            call()


def test_str_replace_needs_exactly_one_match(ws):
    with pytest.raises(WorkspaceError, match="no match"):
        ws.str_replace("stats.py", "nope", "x")
    with pytest.raises(WorkspaceError, match="2 places"):
        ws.str_replace("dup.py", "x = 1", "x = 2")
    assert "edited" in ws.str_replace("dup.py", "x = 1\nx = 1", "x = 2")


def test_create_never_overwrites_and_respects_limits(ws):
    with pytest.raises(WorkspaceError, match="already exists"):
        ws.create("stats.py", "x")
    with pytest.raises(WorkspaceError, match="limit"):
        ws.create("big.py", "x" * 200_000)


def test_view_and_insert(ws):
    assert ws.view("stats.py", [2, 2]).strip().endswith("xs = sorted(xs)")
    ws.insert("stats.py", 0, "# header")
    assert ws.view("stats.py").splitlines()[0].endswith("# header")
    with pytest.raises(WorkspaceError):
        ws.insert("stats.py", 99, "x")


def test_patch_shows_exactly_the_change(ws):
    ws.str_replace("stats.py", "len(xs) // 2", "len(xs) // 3")
    p = ws.patch()
    assert "-    return xs[len(xs) // 2]" in p and "+    return xs[len(xs) // 3]" in p and "tests/" not in p


def test_tamper_detection_and_restore(ws):
    open(os.path.join(ws.root, "tests", "test_stats.py"), "w").write("pass\n")
    assert ws.tampered() == ["tests/test_stats.py"]
    ws.restore_protected()
    assert ws.tampered() == [] and "MedianTests" in open(os.path.join(ws.root, "tests", "test_stats.py")).read()


def test_clip_keeps_head_and_tail():
    s = "HEAD" + "x" * 10_000 + "TAIL"
    c = clip(s, 500)
    assert c.startswith("HEAD") and c.endswith("TAIL") and "omitted" in c and len(c) < 700


def test_parse_unittest():
    out = "FAIL: test_a (x.T)\nERROR: test_b (x.T)\nRan 3 tests in 0.1s\nFAILED (failures=1, errors=1)"
    assert parse_unittest(out) == {"ran": 3, "failing": ["test_a", "test_b"], "ok": False}
    assert parse_unittest("Ran 2 tests in 0.0s\n\nOK")["ok"]


def test_risk_flags_are_information_only():
    assert "network access" in risk_flags("import socket\nsocket.create_connection(('x', 1))")
    assert risk_flags("s = 'so' + 'cket'; __import__(s)") == ["dynamic execution"]       # trivially evaded: flags are not a defence


# ---------------------------------------------------------------- the loop
@pytest.mark.parametrize("task,steps", [("slugify", 13), ("median", 6)])
def test_tdd_loop_solves_tasks(task, steps):
    r = run_job(task, FakeCoder(task), LocalProcessSandbox(LIM))
    assert r.outcome.status == "solved" and r.outcome.steps == steps and r.dir_removed and r.outcome.patch


@needs_ns
def test_tdd_loop_in_the_namespace_sandbox():
    r = run_job("slugify", FakeCoder("slugify"), NamespaceSandbox(LIM))
    assert r.outcome.status == "solved" and "unicodedata" in r.outcome.patch


def test_impossible_task_stops_as_stuck():
    r = run_job("impossible", FakeCoder("impossible"), LocalProcessSandbox(LIM))
    assert r.outcome.status == "stuck" and r.outcome.steps < 12 and "3 times" in r.outcome.stop_reason


def test_cheating_on_tests_is_refused():
    r = run_job("impossible", FakeCoder("impossible", cheat=True), LocalProcessSandbox(LIM))
    errs = [row["error"] for row in r.audit.rows if "error" in row]
    assert any("protected" in e for e in errs) and r.outcome.status != "solved" and "test_calc" not in r.outcome.patch


def test_the_harness_does_not_trust_the_models_claim():
    class Liar:
        def __call__(self, system, messages, tools):
            return [{"type": "text", "text": "All tests pass, I am done!"}]
    r = run_job("median", Liar(), LocalProcessSandbox(LIM))
    assert r.outcome.model_claimed_done and r.outcome.status == "unsolved" and r.outcome.final_tests["ok"] is False


def test_step_limit():
    class Looper:
        n = 0

        def __call__(self, system, messages, tools):
            self.n += 1
            return [{"type": "tool_use", "id": f"t{self.n}", "name": "list_dir", "input": {}}]
    r = run_job("median", Looper(), LocalProcessSandbox(LIM), max_steps=5)
    assert r.outcome.status == "step_limit" and r.outcome.steps == 5


def test_code_that_rewrites_tests_is_caught_by_the_harness():
    class Hacker:
        n = 0

        def __call__(self, system, messages, tools):
            self.n += 1
            if self.n == 1:
                return [{"type": "tool_use", "id": "a", "name": "create", "input": {"path": "hack.py", "file_text": "open('tests/test_stats.py','w').write('import unittest\\n')\n"}}]
            if self.n == 2:
                return [{"type": "tool_use", "id": "b", "name": "run_python", "input": {"path": "hack.py"}}]
            return [{"type": "text", "text": "done"}]
    r = run_job("median", Hacker(), LocalProcessSandbox(LIM))
    assert r.outcome.status == "tampered" and r.outcome.final_tests["ok"] is False


@pytest.mark.parametrize("sb_cls,leaks", [(LocalProcessSandbox, True), pytest.param(NamespaceSandbox, False, marks=needs_ns)])
def test_prompt_injection_blast_radius(sb_cls, leaks):
    ctx = make_ctx()
    try:
        r = run_job("injected", GullibleCoder(), sb_cls(LIM), fill={"SECRET_PATH": ctx.secret_path, "PORT": ctx.listener.port})
        assert r.outcome.status == "solved"                                   # the real task still succeeds either way
        assert (ctx.secret_text.encode() in ctx.listener.data) is leaks
        assert any(row.get("flags") for row in r.audit.rows if row["tool"] == "run_python")
    finally:
        cleanup(ctx)


def test_run_tests_tool_restores_tampered_tests_and_warns(ws):
    from tools import ToolRunner
    open(os.path.join(ws.root, "tests", "test_stats.py"), "w").write("import unittest\nclass T(unittest.TestCase):\n    def test_x(self): pass\n")
    text, _ = ToolRunner(ws, LocalProcessSandbox(LIM)).execute("run_tests", {}, 1)
    assert "WARNING" in text and "test_stats.py" in text
    assert ws.tampered() == [] and "MedianTests" in open(os.path.join(ws.root, "tests", "test_stats.py")).read()
