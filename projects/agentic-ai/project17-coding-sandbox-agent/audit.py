"""Every command, logged. JSON lines: who ran what, where, how it ended. File CONTENTS are never logged, only length + hash."""
import hashlib
import json
import re
import threading
import time

RISKY = [(r"\bimport\s+(socket|subprocess|ctypes|pty|shutil)\b|\bfrom\s+(socket|subprocess|ctypes)\b", "imports a powerful module"),
         (r"os\.system|os\.popen|os\.exec|eval\(|exec\(|__import__", "dynamic execution"),
         (r"/etc/|/root|/proc/|\.ssh|\.aws|\.env\b", "mentions sensitive paths"),
         (r"https?://|\.connect\(|create_connection", "network access")]


def risk_flags(code: str) -> list:
    """INFORMATION for a human reading the log. NOT a defence: obfuscation defeats any scan ('so'+'cket'), which is why the SANDBOX is the control."""
    return sorted({why for pat, why in RISKY if re.search(pat, code)})


def digest(s: str) -> str:
    return f"<{len(s)} chars sha256:{hashlib.sha256(s.encode()).hexdigest()[:10]}>"


class AuditLog:
    def __init__(self, path: str | None = None, job: str = "job"):
        self.path, self.job, self.rows, self._lock = path, job, [], threading.Lock()

    def record(self, **row):
        row = {"ts": round(time.time(), 3), "job": self.job, **row}
        with self._lock:
            self.rows.append(row)
            if self.path:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, default=str) + "\n")
        return row
