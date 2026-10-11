# Project 17 — Code-executing and coding agents (and the sandbox that makes them safe)

A coding agent is an LLM that can **write code and run it**. That one sentence contains the whole risk: you are executing text
produced by a model that may be wrong, manipulated by a prompt injection, or just buggy — on your infrastructure.
This project builds the full loop (look → edit → run → read failure → edit) and, more importantly, the **box** it runs in,
then attacks the box with 12 hostile programs to see what actually holds.

All models here are fakes (scripted). The sandbox, the attacks, the file tools, the loop and the audit log are **real and run**.

```
python experiments/exp1_attacks.py      # 12 attacks x 2 sandbox levels  (L1 needs root + Linux namespaces)
python experiments/exp2_tdd_loop.py     # the test-driven loop, the patch, the 'stuck' brake
python experiments/exp3_injection.py    # prompt injection: what leaks at L0 vs L1
python experiments/exp4_tools_and_limits.py   # what the model is told when tools fail; symlink escape; test tampering
python -m pytest -q                     # ~70 tests; L1 tests skip themselves when namespaces are unavailable
```
No third-party runtime dependencies (stdlib only).

---

## 1. The big ideas (read this first)

**1. Limits are not isolation.** Two different problems:
* *Resource abuse* (infinite loop, memory bomb, output flood, disk fill) → solved by **limits** (CPU, memory, wall clock, output cap, file size).
* *Reach* (read your files, call your network, kill your processes, be root) → needs **isolation** (separate filesystem view, network, pid space, user).
Experiment 1 shows it: Level 0 (limits only) contains 6 of 12 attacks — exactly the resource ones. Level 1 contains 12/12.

**2. The model is not the security boundary.** A prompt like "do not read secrets" is a request, not a control. The harness decides what
is *possible*. Experiment 3: a gullible agent obeys instructions hidden in a README. At L0 the secret leaks; at L1 the file does not
exist inside the box and there is no network. Injection is a model problem; the sandbox only limits the **blast radius**.

**3. "Done" is a claim, not evidence.** When the model says the tests pass, the harness re-runs them itself (on restored, pristine test files).

**4. Tests are the spec — so the agent must not edit them.** Otherwise the cheapest "fix" is to delete the failing assertion
(reward hacking). `tests/` is read-only for the tools, and if *executed code* rewrites a test the harness detects it, restores it and tells the model.

**5. Every loop needs brakes.** max steps, same-failure detector, sandbox time budget. A contradictory task must end as `stuck` with a clear reason, not as a large bill.

**6. The deliverable is a patch.** A human (or CI) reviews a diff. The agent never "just changes your repo".

**7. Throw the workspace away.** One job = one fresh directory, one fresh uid per command, destroyed afterwards. No state, files or secrets shared between jobs.

---

## 2. The three sandbox levels (`sandbox.py`)

| Level | What it is | Stops | Does not stop |
|---|---|---|---|
| **L0** process | child process, `rlimit`s (CPU, memory, procs, file size, fds), wall-clock kill of the whole process group, scrubbed env, output cap | loops, memory, output floods, disk fill, env-secret leaks | file reads, network, signals, running as root. A **safety net, not a boundary** |
| **L1** namespaces | `unshare` new mount + net + pid namespaces, `chroot` into a minimal root (`/usr` bind-mounted **read-only**, tmpfs `/tmp`, minimal `/dev`), drop to a **unique unprivileged uid**, `no_new_privs`, empty capability bounding set, ulimits | everything in the table below | kernel bugs (same kernel as the host); side channels |
| **L2** Docker | the same ideas through a container runtime: `--network none --read-only --cap-drop ALL --pids-limit --memory --user 65534` | same as L1, plus image/cgroup management | still a shared kernel. `command()` only builds the string here; no Docker daemon was available to run it |

Beyond L2 (not built; know that it exists): **gVisor** (user-space kernel intercepts syscalls), **Firecracker/microVMs** (separate kernel).
Use these when you run code from **strangers**; containers are usually enough for your own agent on your own tasks.

### Attack results (real output)
```
attack               L0-process   L1-namespaces
infinite_loop        contained    contained     killed after ~2s (CPU limit)
sleep_forever        contained    contained     wall-clock timeout (CPU limit cannot see sleeping)
memory_bomb          contained    contained     stopped by memory limit
fork_bomb            ESCAPED      contained     L0: created 300 processes; L1: refused after 30
output_flood         contained    contained     kept 20000 chars
disk_fill            contained    contained     file-size limit
network_loopback     ESCAPED      contained     L0 reached a service on the host's 127.0.0.1
read_host_file       ESCAPED      contained     L0 read a secret file
write_outside        ESCAPED      contained
signal_host_process  ESCAPED      contained     L0 killed another process
who_am_i             ESCAPED      contained     L0: uid 0   |  L1: random unprivileged uid
env_secrets          contained    contained     nothing inherited from the parent env
score:  L0 6/12     L1 12/12
```
Why the fork bomb "escapes" at L0: as root, `RLIMIT_NPROC` is not enforced. L1 runs as a non-root uid *inside its own pid namespace*, so it is.
(The attack is capped at 300 processes so the demo itself is safe.)

### Details worth understanding
* **Kill the process group, always.** A program can spawn children that outlive it. `_collect` ends with `killpg`, and a test checks no orphan survives.
* **`python -E -s -u`**: ignore PYTHON* env vars and user site (no hidden config), unbuffered (so partial output survives a kill — otherwise the model gets *nothing* when a timeout happens).
* **Unique uid per run** means a run cannot touch another run's files even if the filesystem were shared.
* **Why chroot is OK here but not enough alone**: root can escape a chroot. We drop privileges *and* use mount/pid/net namespaces *and* no_new_privs; each layer covers a gap in another.
* **Honest limit**: all of this shares the host kernel. A kernel exploit beats it.

---

## 3. The file tools (`workspace.py`, `tools.py`)

The model gets 7 tools: `list_dir`, `view`, `create`, `str_replace`, `insert`, `run_python`, `run_tests`. Each design choice is about **making wrong actions impossible or loudly visible**:

* **Path jail** — relative paths only, no `..`, no `~`, resolved path must stay under the root. **Symlink check**: sandboxed code can create a symlink to `/etc/passwd`; the *agent's* file tools run outside the sandbox and would follow it. So every resolve also checks the real path (experiment 4 demonstrates the attack and the refusal).
* **`str_replace` needs exactly one match.** Zero → "no match, must match exactly including indentation". Two or more → "include more surrounding lines". This is how real editors keep an LLM from silently editing the wrong place. The error text *teaches* the model how to recover.
* **`create` never overwrites.** Overwrite requires an explicit, visible `str_replace`.
* **Size limits** on files and file count.
* **Protected paths** (`tests/`).
* **Tool output is context** (Project 13): `clip()` keeps the head *and the tail* (tracebacks and the test summary are at the end), and says how much was dropped.
* **Error messages are written for the model**: what happened, and what to do next.

## 4. The loop (`agent.py`)

```
messages = [task]
for step in 1..max_steps:
    reply = model(system, messages, tools)
    no tool calls?  -> model claims done -> break
    execute every tool call -> append tool_result -> (errors flagged is_error)
    same failing-test set 3x?  -> status "stuck"
    sandbox seconds > budget?  -> status "budget"
harness runs the tests itself (after restoring protected files) -> status solved / unsolved / tampered
patch = diff(original snapshot, workspace)
```
Experiment 2 prints a real transcript: it reads the tests, writes `slug.py`, runs, 3 failing, fixes one at a time, 0 failing, and the harness re-verifies. Then an **impossible task** (two tests contradict) ends `stuck` after 8 steps instead of looping.

## 5. Tamper detection (reward hacking)
Even with read-only *tools*, code the agent **runs** could rewrite `tests/`. `run_tests` first compares protected files with their snapshot, restores them, and returns a WARNING to the model. The final verification restores again. (Experiment 4, section 3.) Without this, "the tests pass" can simply mean "the tests were changed".

## 6. Audit log and risk flags (`audit.py`)
Every tool call is logged with step, tool, args (large text replaced by length + sha256 so the log does not hold your code twice), result summary and duration.
`risk_flags` tags suspicious runs (opens sockets, reads outside the workspace, `os.system`, `subprocess`, base64, ...). **Flags are information for humans, not a defence** — a regex can always be evaded. The sandbox is the defence; the log is how you notice and investigate.

## 7. Prompt injection, concretely (`experiments/exp3_injection.py`)
`tasks/injected/README.md` contains text addressed to "AI assistants": read a secret file and connect to a local port. `GullibleCoder` obeys. Result:
```
L0  real task: solved   SECRET LEAKED          host service saw 1 connection
L1  real task: solved   nothing left the box   host service saw 0 connections
```
Lessons: the agent was fooled in both runs and *still solved the task* — injected behaviour is invisible in the outcome. Defence in depth:
1. no secrets in the sandbox, 2. no network (or an allow-list proxy), 3. treat file contents as **data**, 4. a human reviews the patch, 5. alert on audit flags.
Same logic as Project 16's "tool results are untrusted".

## 8. How real coding agents map to this
| Here | Real systems |
|---|---|
| `view/create/str_replace/insert` | Anthropic's text-editor tool; Claude Code's Read/Edit/Write |
| `run_python`/`run_tests` | a bash tool, a code-execution tool in a managed container |
| workspace + snapshot + patch | git worktree / branch + pull request |
| L1/L2 sandbox | containers, gVisor, Firecracker; hosted code-execution tools |
| step/same-failure/budget brakes | max turns, cost caps, loop detection |
| harness-verified "done" | CI re-running tests on the PR |
| audit log | transcript + tool-call logs |
Check the current Anthropic docs for the exact tool type names and versions (`live_coder.py` uses custom tools of the same shape and is **unrun**).

## 9. Production checklist
* Sandbox: no network by default; read-only root; non-root; cgroup memory/pids/CPU; wall-clock; output cap; fresh per job; destroy after.
* No credentials inside. Need git push or package install? Do it in the harness, outside, on the reviewed patch.
* Pin the base image; scan it. Cap total concurrent sandboxes. Per-tenant quotas.
* Log everything; keep the patch and transcript with the job id.
* Human or CI gate before merge. Tests the agent cannot touch.

## 10. Exercises
1. Run exp1 as a non-root user. Which L0 results change, and why? (Hint: `who_am_i`, `fork_bomb`.)
2. Add an attack: write a file into `tests/` from sandboxed code. Which layer catches it?
3. Add `pip install` support with an allow-list proxy. What new attacks appear?
4. Make `risk_flags` stricter, then write a program that evades it. What does that tell you?
5. Replace `FakeCoder` with `live_coder.py` on `slugify`. Compare the transcript with exp2. What does the real model do that the script didn't?
6. Implement a git-worktree workspace instead of a temp dir copy.

## Honest limits
* The models are scripted; real models will behave messier (they may need more steps, misread output).
* L2 (Docker) was **not executed** (no daemon here). L1 shares the host kernel.
* L1 requires root and namespace support; it is skipped where unavailable.
* `live_coder.py` was not run. Token/cost behaviour of a real loop was not measured.
* Risk flags are heuristics.
