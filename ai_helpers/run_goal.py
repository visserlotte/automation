"""
Run-Goal Helper
Launches master_ai.py goals in a background thread and streams live
output to logs/current_run.log.  Always recreates the log directory and
keeps a symlink pointing at the latest run_*.log.
"""

from __future__ import annotations

import datetime
import pathlib
import subprocess
import sys
import threading
import time

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
LOG_DIR = ROOT_DIR / "logs"
STREAM_FILE = LOG_DIR / "current_run.log"


def _safe_append(text: str) -> None:
    """Append to current_run.log, recreating dir/link if needed."""
    while True:
        try:
            STREAM_FILE.parent.mkdir(parents=True, exist_ok=True)
            with STREAM_FILE.open("a") as f:
                f.write(text)
            break
        except FileNotFoundError:
            time.sleep(0.05)


def _update_symlink(target: pathlib.Path) -> None:
    try:
        STREAM_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    try:
        STREAM_FILE.symlink_to(target.name)  # relative link
    except Exception as e:
        print(f"[run_goal] symlink warn: {e}")


def _runner(goal: str) -> None:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    hist = LOG_DIR / f"run_{ts}.log"
    header = f"---\nRunning goal: {goal}\n---\n"

    STREAM_FILE.parent.mkdir(parents=True, exist_ok=True)
    _update_symlink(hist)
    _safe_append(header)

    with hist.open("w") as lf:
        lf.write(header)

        cmd = [
            sys.executable,
            str(ROOT_DIR / "master_ai.py"),
            "--goal",
            goal,
            "--self-build",
            "--email",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in proc.stdout or []:
            _safe_append(line)
            lf.write(line)


def run_goal_async(goal: str) -> str:
    threading.Thread(target=_runner, args=(goal,), daemon=True).start()
    return f"🛠️  Running goal: {goal}"
