import os
import tempfile

import pytest
from conftest import needs_ns

from attacks import ATTACKS, run_attack
from sandbox import DockerSandbox, Limits, LocalProcessSandbox

RESOURCE = {"infinite_loop", "sleep_forever", "memory_bomb", "output_flood", "disk_fill", "env_secrets"}
REACH = {"fork_bomb", "network_loopback", "read_host_file", "write_outside", "signal_host_process", "who_am_i"}


@pytest.mark.parametrize("attack", [a for a in ATTACKS], ids=lambda a: a.name)
def test_level0_stops_resource_abuse(attack, ctx, l0):
    ok, evidence, _ = run_attack(l0, attack, ctx)
    if attack.name in RESOURCE:
        assert ok, evidence


@pytest.mark.parametrize("name", sorted(REACH))
def test_level0_is_not_a_security_boundary(name, ctx, l0):
    """Documented on purpose: a plain process cannot be trusted with hostile code."""
    attack = next(a for a in ATTACKS if a.name == name)
    ok, evidence, _ = run_attack(l0, attack, ctx)
    assert not ok, f"L0 unexpectedly contained {name}: {evidence}"


@needs_ns
@pytest.mark.parametrize("attack", ATTACKS, ids=lambda a: a.name)
def test_level1_contains_everything(attack, ctx, l1):
    ok, evidence, _ = run_attack(l1, attack, ctx)
    assert ok, f"{attack.name}: {evidence}"


@needs_ns
def test_each_run_gets_its_own_uid_and_jail_is_destroyed(l1):
    d = tempfile.mkdtemp()
    os.chmod(d, 0o755)
    open(os.path.join(d, "m.py"), "w").write("import os\nprint(os.getuid())\n")
    before = set(os.listdir(tempfile.gettempdir()))
    uids = {l1.run(d, l1.python_argv(["/work/m.py"])).stdout.strip() for _ in range(3)}
    assert len(uids) == 3 and "0" not in uids
    assert not [x for x in set(os.listdir(tempfile.gettempdir())) - before if x.startswith("jail-")]


@needs_ns
def test_jail_filesystem_is_minimal_and_usr_is_read_only(l1):
    d = tempfile.mkdtemp()
    os.chmod(d, 0o755)
    open(os.path.join(d, "m.py"), "w").write(
        "import os\nprint(sorted(os.listdir('/')))\ntry:\n    open('/usr/x', 'w')\nexcept OSError as e:\n    print('usr:', type(e).__name__)\n"
        "print(os.path.exists('/root'), os.path.exists('/home'), os.path.exists('/etc/passwd'))\n")
    out = l1.run(d, l1.python_argv(["/work/m.py"])).stdout
    assert "usr: OSError" in out or "usr: PermissionError" in out or "usr: Read" in out
    assert "False False False" in out and "'home'" not in out


def test_environment_is_not_inherited(l0, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-not-leak")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy")
    d = tempfile.mkdtemp()
    open(os.path.join(d, "m.py"), "w").write("import os\nprint(sorted(os.environ))\n")
    out = l0.run(d, l0.python_argv(["m.py"])).stdout
    assert "ANTHROPIC" not in out and "PROXY" not in out


def test_output_cap_and_wall_clock(l0):
    d = tempfile.mkdtemp()
    open(os.path.join(d, "m.py"), "w").write("import time\nprint('x' * 100)\ntime.sleep(60)\n")
    r = LocalProcessSandbox(Limits(wall_s=1)).run(d, l0.python_argv(["m.py"]))
    assert r.timed_out and r.duration_s < 3 and "xxx" in r.stdout


def test_docker_command_has_the_hardening_flags():
    cmd = DockerSandbox(Limits(mem_mb=256, max_procs=16)).command("/tmp/j", ["python", "m.py"])
    s = " ".join(cmd)
    for flag in ("--network none", "--read-only", "--cap-drop ALL", "no-new-privileges", "--pids-limit 16", "--memory 256m", "--user 65534:65534"):
        assert flag in s
    assert cmd[-2:] == ["python", "m.py"] and "/tmp/j:/work:rw" in s


@needs_ns
def test_usr_is_mounted_read_only_in_the_jail(l1):
    d = tempfile.mkdtemp()
    os.chmod(d, 0o755)
    open(os.path.join(d, "m.py"), "w").write("for line in open('/proc/self/mountinfo'):\n    f = line.split()\n    if f[4] in ('/usr', '/work', '/tmp'):\n        print(f[4], f[5])\n")
    out = l1.run(d, l1.python_argv(["/work/m.py"])).stdout
    usr = [ln for ln in out.splitlines() if ln.startswith("/usr ")]
    assert usr and "ro" in usr[0].split()[1].split(",")
    tmp = [ln for ln in out.splitlines() if ln.startswith("/tmp ")]
    assert tmp and "nosuid" in tmp[0]


@pytest.mark.parametrize("level", ["l0", pytest.param("l1", marks=needs_ns)])
def test_orphaned_children_do_not_outlive_the_run(level, request):
    import time
    sb = request.getfixturevalue(level)
    d = tempfile.mkdtemp()
    os.chmod(d, 0o777)
    open(os.path.join(d, "m.py"), "w").write("import os, time\nif os.fork() == 0:\n    time.sleep(1.5)\n    open('alive.txt', 'w').write('x')\n    os._exit(0)\nprint('parent done')\n")
    sb.run(d, sb.python_argv(["/work/m.py" if level == "l1" else "m.py"]))
    time.sleep(2.5)
    assert not os.path.exists(os.path.join(d, "alive.txt"))
