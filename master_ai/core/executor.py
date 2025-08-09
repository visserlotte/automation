from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ALLOWED_CMDS = {"python", "pytest", "pip", "echo", "ls", "cat", "mkdir", "touch", "sh", "bash"}


@dataclass
class ExecResult:
    returncode: int
    stdout: str
    stderr: str
    cmd: list[str]
    cwd: str


class Executor:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.sandbox = run_dir / "sandbox"
        self.logs = run_dir / "logs"
        self.sandbox.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        cmd: Sequence[str],
        *,
        cwd: Path | None = None,
        env: dict | None = None,
        timeout: int = 300,
    ) -> ExecResult:
        if cmd and cmd[0] not in ALLOWED_CMDS:
            raise RuntimeError(f"Command not allowed: {cmd[0]}")
        wdir = cwd or self.sandbox
        penv = os.environ.copy()
        if env:
            penv.update(env)
        p = subprocess.run(
            list(cmd),
            cwd=str(wdir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=penv,
        )
        ts = time.strftime("%Y%m%d_%H%M%S")
        (self.logs / f"cmd_{ts}.log").write_text(
            json.dumps(
                {
                    "cmd": cmd,
                    "cwd": str(wdir),
                    "rc": p.returncode,
                    "stdout": p.stdout,
                    "stderr": p.stderr,
                },
                indent=2,
            )
        )
        return ExecResult(p.returncode, p.stdout, p.stderr, list(cmd), str(wdir))

    def stage_project(self, src: Path) -> Path:
        """Copy a project into the sandbox (shallow) and return the dest path."""
        dest = self.sandbox / src.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        return dest
