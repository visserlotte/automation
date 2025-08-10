from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Where runs land by default (used by other modules too)
RUNS_ROOT = Path("artifacts/runs")


def ensure_dir(p: Path | str) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _bash_available() -> bool:
    try:
        subprocess.run(
            ["/bin/bash", "-lc", "true"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def run_stream(
    cmd: str,
    *,
    cwd: Path | str,
    env_add: dict[str, str] | None = None,
    safe_mode: bool = True,
) -> subprocess.Popen:
    """
    Start a subprocess and stream its stdout lines.
    - `safe_mode` is accepted for compatibility; for now both modes execute via a shell.
      If you want stricter sandboxing, wire your policy here (e.g., allowlist commands).
    Returns the Popen; iterate over `proc.stdout` to stream lines, then `proc.wait()`.
    """
    workdir = Path(cwd)
    workdir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if env_add:
        env.update(env_add)

    # Use bash if available for nicer -lc behavior; otherwise fall back to /bin/sh
    if _bash_available():
        args = ["/bin/bash", "-lc", cmd]
    else:
        args = ["/bin/sh", "-c", cmd]

    # NOTE: If you later implement a strict "safe_mode", this is the place to add checks:
    # e.g., verify the command against an allowlist before executing.

    proc = subprocess.Popen(
        args,
        cwd=str(workdir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    return proc
