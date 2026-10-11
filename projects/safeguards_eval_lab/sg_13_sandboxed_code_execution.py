"""SG-13  Sandboxing: running UNTRUSTED code (e.g. code an LLM wrote) with layered defences.
Run: python sg_13_sandboxed_code_execution.py
Layer 1 = static check (AST).  Layer 2 = separate process with CPU/memory/file limits, empty env, temp dir, timeout.
IMPORTANT: this is a teaching sandbox, NOT a security boundary. See the sandbox ladder printed at the end."""
import ast, os, subprocess, sys, tempfile

try:
    import resource                       # Linux/macOS only. On Windows the limits below are skipped.
except ImportError:
    resource = None

ALLOWED_IMPORTS = {"math", "json", "statistics", "random"}
BANNED_NAMES = {"open", "exec", "eval", "compile", "input", "breakpoint", "globals", "locals", "vars",
                "getattr", "setattr", "delattr"}


def static_check(code: str) -> list[str]:
    """LAYER 1: reject obviously dangerous code BEFORE running anything."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            problems += [f"import '{a.name}' not allowed" for a in node.names if a.name.split(".")[0] not in ALLOWED_IMPORTS]
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                problems.append(f"import from '{node.module}' not allowed")
        elif isinstance(node, ast.Name) and (node.id in BANNED_NAMES or node.id.startswith("__")):
            problems.append(f"name '{node.id}' not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            problems.append(f"attribute '{node.attr}' not allowed (classic sandbox-escape route)")
    return problems


def run_sandboxed(code: str, timeout_s: int = 2, mem_mb: int = 256, use_static_check: bool = True) -> str:
    if use_static_check:
        problems = static_check(code)
        if problems:
            return "REJECTED before running: " + "; ".join(sorted(set(problems)))

    def apply_limits():                                   # runs inside the child process just before it starts
        if resource:
            resource.setrlimit(resource.RLIMIT_CPU, (timeout_s, timeout_s))                 # CPU seconds
            resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 2**20, mem_mb * 2**20))        # memory
            resource.setrlimit(resource.RLIMIT_FSIZE, (2**20, 2**20))                       # max file it may write: 1 MB

    with tempfile.TemporaryDirectory() as workdir:        # LAYER 2: its own throwaway working directory
        script = os.path.join(workdir, "job.py")
        with open(script, "w") as f:
            f.write(code)
        env = {"SYSTEMROOT": os.environ["SYSTEMROOT"]} if "SYSTEMROOT" in os.environ else {}   # EMPTY env: no API keys leak in
        try:
            r = subprocess.run([sys.executable, "-I", script], cwd=workdir, env=env, capture_output=True, text=True,
                               timeout=timeout_s + 1, preexec_fn=apply_limits if resource else None)
        except subprocess.TimeoutExpired:
            return "KILLED: wall-clock timeout"
        if r.returncode < 0:
            return f"KILLED by signal {-r.returncode} (CPU-time limit exceeded)"
        if r.returncode != 0:
            err = (r.stderr.strip().splitlines() or ["(no stderr)"])[-1]
            return f"FAILED (exit {r.returncode}): {err[:90]}"
        return "OK: " + r.stdout.strip()[:90]


os.environ["FAKE_SECRET_API_KEY"] = "sk-this-must-never-leak-123456"

print("=== with BOTH layers ===")
for name, code in [
    ("harmless maths",          "print(sum(i*i for i in range(10)))"),
    ("import os",               "import os\nprint(os.listdir('/'))"),
    ("read a system file",      "print(open('/etc/passwd').read())"),
    ("dunder escape",           "print(().__class__.__bases__[0].__subclasses__())"),
    ("infinite loop",           "while True:\n    pass"),
    ("memory bomb",             "x = 'a' * (10**10)\nprint(len(x))"),
]:
    print(f"{name:20} -> {run_sandboxed(code)}")

print("\n=== Layer 2 ALONE (static check switched off) - to see what the process limits do and do NOT stop ===")
for name, code in [
    ("infinite loop",           "while True:\n    pass"),
    ("memory bomb",             "x = 'a' * (10**10)\nprint(len(x))"),
    ("steal env secret",        "import os\nprint(os.environ.get('FAKE_SECRET_API_KEY'))"),
    ("read a system file",      "print(open('/etc/hostname').read()[:20])"),
]:
    print(f"{name:20} -> {run_sandboxed(code, use_static_check=False)}")

print("""
What just happened:
  - empty environment: the child could not see FAKE_SECRET_API_KEY            (stopped)
  - CPU / memory limits and timeout stopped the loop and the memory bomb       (stopped)
  - reading a system file STILL WORKED without the static check                (NOT stopped)
    -> process limits do not isolate the filesystem or the network. That is why real systems add:

THE SANDBOX LADDER (weakest -> strongest)
  1. Static checks + restricted builtins   (this file's layer 1)   easy to bypass, first filter only
  2. Separate OS process + rlimits + empty env + temp dir (layer 2)  stops runaway resources, not file/network access
  3. Container (Docker) with: non-root user, read-only root FS, no network, --memory/--cpus/--pids-limit,
     dropped capabilities, seccomp profile                          shares the host kernel
  4. gVisor / Kata Containers              a user-space kernel or lightweight VM between the code and the host
  5. MicroVM (Firecracker) or a full VM    separate kernel per job; used by AWS Lambda and many AI code-interpreter services
  6. WebAssembly runtime (Pyodide, Wasmtime)  capability-based: the code can only touch what you hand it
  Managed options: E2B, Modal, Daytona, Cloudflare/AWS code-interpreter sandboxes.
RULE: never run LLM-written code in your own application process, and never rely on one layer.
""")
