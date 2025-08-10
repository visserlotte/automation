from __future__ import annotations

import subprocess
from collections.abc import Sequence

ALLOWED = {
    "python",
    "pytest",
    "pip",
    "echo",
    "ls",
    "cat",
    "mkdir",
    "touch",
    "sh",
    "bash",
}


def run(
    cmd: Sequence[str], cwd: str | None = None, timeout: int = 120
) -> subprocess.CompletedProcess:
    if cmd and cmd[0] not in ALLOWED:
        raise RuntimeError(f"Command not allowed: {cmd[0]}")
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
