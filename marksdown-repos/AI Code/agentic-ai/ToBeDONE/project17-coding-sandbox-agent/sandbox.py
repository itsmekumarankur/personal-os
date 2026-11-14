"""Where untrusted code runs. Three levels, because 'sandbox' is not one thing:

  LEVEL 0  LocalProcessSandbox   a child process with resource limits, a scrubbed environment and a throw-away working directory.
                                 Stops: runaway CPU/memory/output/time, leaked environment secrets.
                                 Does NOT stop: reading any file the user can read, writing elsewhere, using the network, killing other processes.
                                 => a SAFETY NET against accidents, NOT a security boundary.

  LEVEL 1  NamespaceSandbox      Linux namespaces + chroot, built from scratch in ~40 lines of shell so you can see every ingredient:
                                   new MOUNT namespace   the code sees only a tiny root we assemble: /usr read-only, /work (the job), /tmp (small tmpfs)
                                   new NETWORK namespace no interfaces at all (not even the host's loopback) -> no network
                                   new PID namespace     it cannot see or signal any host process; a fork bomb stays inside
                                   chroot                no path leads out of the assembled root
                                   unique unprivileged uid, no capabilities, no_new_privs, ulimits (CPU, memory, processes, file size, open files)
                                 Needs root (or CAP_SYS_ADMIN) on Linux. Shares the host KERNEL: a kernel bug can still escape.

  LEVEL 2  DockerSandbox         the same ideas via a container runtime (cgroups for real memory/CPU/pids limits, seccomp, read-only rootfs).
                                 The command is built and unit-tested here; it was NOT executed (no Docker daemon in this environment).
                                 For hostile code at scale add a stronger boundary: gVisor (user-space kernel) or Firecracker (micro-VM).

Rule of thumb: the sandbox is the control. Scanners ("does the code import socket?") only help you read logs; attackers rename things.
"""
import os
import resource
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field


@dataclass
class Limits:
    wall_s: float = 10.0            # real time; catches sleeping and blocking, which CPU limits miss
    cpu_s: int = 5                  # CPU seconds; catches busy loops
    mem_mb: int = 400               # address space (RLIMIT_AS). Crude: real memory accounting needs cgroups
    max_procs: int = 32             # processes/threads for the sandbox uid
    file_mb: int = 16               # largest single file it may write
    open_files: int = 64
    output_bytes: int = 20_000      # stdout+stderr we keep; more is discarded and the run is killed


@dataclass
class Result:
    exit_code: int | None
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False
    output_truncated: bool = False
    signal: str | None = None
    level: str = ""
    notes: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def _collect(proc: subprocess.Popen, limits: Limits) -> tuple:
    """Read stdout/stderr with a hard cap and a wall-clock deadline. Kills the whole process group when either is exceeded."""
    buf = {"out": bytearray(), "err": bytearray()}
    state = {"truncated": False, "total": 0}
    lock = threading.Lock()

    def pump(stream, key):
        while True:
            chunk = stream.read1(4096) if hasattr(stream, "read1") else stream.read(4096)
            if not chunk:
                return
            with lock:
                room = limits.output_bytes - state["total"]
                if room > 0:
                    buf[key] += chunk[:room]
                state["total"] += len(chunk)
                if state["total"] > limits.output_bytes and not state["truncated"]:
                    state["truncated"] = True
                    _kill(proc)

    threads = [threading.Thread(target=pump, args=(proc.stdout, "out"), daemon=True), threading.Thread(target=pump, args=(proc.stderr, "err"), daemon=True)]
    for t in threads:
        t.start()
    timed_out = False
    try:
        proc.wait(timeout=limits.wall_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill(proc)
        proc.wait()
    _kill(proc)                                           # stragglers (orphaned children) must not outlive the run
    for t in threads:
        t.join(timeout=2)
    return bytes(buf["out"]).decode("utf-8", "replace"), bytes(buf["err"]).decode("utf-8", "replace"), timed_out, state["truncated"]


def _kill(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)               # the whole group, including grandchildren
    except (ProcessLookupError, PermissionError):
        pass


def _finish(proc, out, err, t0, timed_out, truncated, level, notes=None) -> Result:
    code, sig = proc.returncode, None
    if code is not None and code < 0:
        sig, code = signal.Signals(-code).name, None
    elif code is not None and code > 128 and code - 128 in (9, 24, 25, 11, 6):      # shell reports 128+N when a child died of signal N
        sig = signal.Signals(code - 128).name
    return Result(code, out, err, round(time.monotonic() - t0, 3), timed_out, truncated, sig, level, notes or [])


# ============================================================ level 0
class LocalProcessSandbox:
    level = "L0-process"

    def __init__(self, limits: Limits | None = None, python: str | None = None):
        self.limits, self.python = limits or Limits(), python or shutil.which("python3") or "python3"

    def _preexec(self):
        L = self.limits

        def apply():
            os.setsid()
            resource.setrlimit(resource.RLIMIT_CPU, (L.cpu_s, L.cpu_s))
            resource.setrlimit(resource.RLIMIT_AS, (L.mem_mb << 20, L.mem_mb << 20))
            resource.setrlimit(resource.RLIMIT_FSIZE, (L.file_mb << 20, L.file_mb << 20))
            resource.setrlimit(resource.RLIMIT_NOFILE, (L.open_files, L.open_files))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        return apply

    def run(self, workdir: str, argv: list, stdin: str | None = None) -> Result:
        env = {"PATH": "/usr/bin:/bin", "HOME": workdir, "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}       # nothing inherited: no API keys, no proxy vars
        t0 = time.monotonic()
        proc = subprocess.Popen(argv, cwd=workdir, env=env, stdin=subprocess.PIPE if stdin else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                preexec_fn=self._preexec())
        if stdin:
            proc.stdin.write(stdin.encode())
            proc.stdin.close()
        out, err, to, tr = _collect(proc, self.limits)
        return _finish(proc, out, err, t0, to, tr, self.level)

    def python_argv(self, args: list) -> list:
        return [self.python, "-E", "-s", "-u", *args]


# ============================================================ level 1
_BOOT = r"""
set -e
R="$1"; WORK="$2"; UID_="$3"; shift 3
mkdir -p "$R/usr" "$R/work" "$R/proc" "$R/tmp" "$R/dev" "$R/etc"
mount --bind /usr "$R/usr"; mount -o remount,ro,bind "$R/usr"                  # system files visible, read-only
for d in lib lib64 bin sbin; do [ -e "/$d" ] && ln -s "usr/$d" "$R/$d" || true; done
mount --bind "$WORK" "$R/work"                                                  # the ONLY writable thing that survives: the job directory
mount -t tmpfs -o size=32m,mode=1777,nosuid,nodev tmpfs "$R/tmp"               # scratch space, small, gone afterwards
mount -t proc proc "$R/proc"                                                    # shows only processes of the NEW pid namespace
for n in null zero urandom; do touch "$R/dev/$n"; mount --bind "/dev/$n" "$R/dev/$n"; done
exec chroot "$R" /usr/bin/setpriv --reuid="$UID_" --regid="$UID_" --clear-groups --no-new-privs --bounding-set=-all "$@"
"""


class NamespaceSandbox:
    level = "L1-namespaces"

    def __init__(self, limits: Limits | None = None):
        self.limits = limits or Limits()
        self._next_uid = 20000 + (os.getpid() % 20000)

    @staticmethod
    def available() -> bool:
        if os.geteuid() != 0 or not all(shutil.which(x) for x in ("unshare", "chroot", "setpriv", "bash")):
            return False
        r = subprocess.run(["unshare", "-m", "-n", "-p", "-f", "true"], capture_output=True)
        return r.returncode == 0

    def run(self, workdir: str, argv: list, stdin: str | None = None) -> Result:
        """argv are paths INSIDE the jail, e.g. ['/usr/bin/python3.13', '-I', '/work/main.py']."""
        L = self.limits
        self._next_uid += 1
        uid = self._next_uid                                      # a different uid per run, so NPROC limits and file ownership never overlap
        root = tempfile.mkdtemp(prefix="jail-")
        os.chmod(root, 0o755)
        shutil.chown(workdir, uid, uid)
        for dp, dns, fns in os.walk(workdir):
            for n in dns + fns:
                try:
                    os.chown(os.path.join(dp, n), uid, uid, follow_symlinks=False)
                except OSError:
                    pass
        ulimits = (f"ulimit -t {L.cpu_s}; ulimit -v {L.mem_mb * 1024}; ulimit -u {L.max_procs}; ulimit -f {L.file_mb * 1024}; "
                   f"ulimit -n {L.open_files}; ulimit -c 0; cd /work; \"$@\"; exit $?")      # no exec: bash stays pid 1 of the namespace, reaps children and reports 128+N for a killed child
        inner = ["/usr/bin/env", "-i", "PATH=/usr/bin:/bin", "HOME=/tmp", "LANG=C.UTF-8", "PYTHONDONTWRITEBYTECODE=1",
                 "/usr/bin/bash", "-c", ulimits, "sandbox", *argv]
        cmd = ["unshare", "-m", "-n", "-p", "-f", "--mount-proc", "bash", "-c", _BOOT, "boot", root, os.path.abspath(workdir), str(uid), *inner]
        t0 = time.monotonic()
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE if stdin else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                                    env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})                 # the host environment is not even passed to the launcher
            if stdin:
                proc.stdin.write(stdin.encode())
                proc.stdin.close()
            out, err, to, tr = _collect(proc, L)
        finally:
            _umount_all(root)
            shutil.rmtree(root, ignore_errors=True)                # destroy the jail after EVERY run
        return _finish(proc, out, err, t0, to, tr, self.level)

    def python_argv(self, args: list) -> list:
        return [PY_IN_JAIL, "-E", "-s", "-u", *args]


def _umount_all(root: str):
    """Mounts live inside the child's private namespace and vanish with it; this is belt-and-braces for a crashed launcher."""
    subprocess.run(["bash", "-c", f"grep -q ' {root}' /proc/mounts && umount -R -l '{root}' || true"], capture_output=True)


PY_IN_JAIL = os.path.realpath(shutil.which("python3") or "/usr/bin/python3")


# ============================================================ level 2
class DockerSandbox:
    level = "L2-docker"

    def __init__(self, limits: Limits | None = None, image: str = "python:3.12-slim"):
        self.limits, self.image = limits or Limits(), image

    def command(self, workdir: str, argv: list) -> list:
        L = self.limits
        return ["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
                "--memory", f"{L.mem_mb}m", "--memory-swap", f"{L.mem_mb}m", "--cpus", "0.5", "--pids-limit", str(L.max_procs),
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534", "--ulimit", f"cpu={L.cpu_s}",
                "--ulimit", f"fsize={L.file_mb << 20}", "--ulimit", f"nofile={L.open_files}", "-v", f"{os.path.abspath(workdir)}:/work:rw", "-w", "/work",
                "--env", "HOME=/tmp", "--env", "PYTHONDONTWRITEBYTECODE=1", self.image, *argv]

    def run(self, workdir: str, argv: list, stdin: str | None = None) -> Result:
        t0 = time.monotonic()
        proc = subprocess.Popen(self.command(workdir, argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        out, err, to, tr = _collect(proc, self.limits)
        return _finish(proc, out, err, t0, to, tr, self.level)

    def python_argv(self, args: list) -> list:
        return ["python", "-E", "-s", "-u", *args]
