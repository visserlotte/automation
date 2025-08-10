from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from master_ai.agents.planner import Step, make_plan
from master_ai.runtime.events import EventBus, log
from master_ai.runtime.fileops import (
    apply_structured_edits,
    patch_file,
    scaffold_layout,
    write_file,
)
from master_ai.runtime.net import fetch_file
from master_ai.runtime.utils import run_stream


@dataclass
class Agent:
    goal: str
    root: Path
    safe_mode: bool = True

    def run(self) -> int:
        run_id = time.strftime("%Y%m%d_%H%M%S")
        run_dir = self.root / run_id
        logs_dir = run_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        bus = EventBus(run_dir)
        log(
            "run_started",
            {"run_id": run_id, "goal": self.goal, "safe": self.safe_mode},
            bus=bus,
        )

        try:
            steps = make_plan(self.goal)
        except Exception as e:  # pragma: no cover
            log("log", {"step": 0, "line": f"planner error: {e}"}, bus=bus)
            log("run_finished", {"result": "FAILED"}, bus=bus)
            print(f"[agent] run={run_id} result=FAILED")
            print(f"[agent] events: {run_dir / 'events.jsonl'}")
            print(f"[agent] logs:   {logs_dir}")
            return 1

        log("plan_ready", {"steps": [s.__dict__ for s in steps]}, bus=bus)
        log("progress", {"current": 0, "total": len(steps), "eta": None}, bus=bus)

        try:
            for idx, step in enumerate(steps, start=1):
                log(
                    "thought",
                    {"text": f"Step {idx}/{len(steps)}: {step.desc}"},
                    bus=bus,
                )
                logfile: Path | None = None

                # Retry loop (default 1 attempt)
                attempts = getattr(step, "retries", 1) or 1
                allow_fail = bool(getattr(step, "allow_fail", False))
                timeout_s = getattr(step, "timeout", None)  # seconds or None
                rc = 0
                t0_step = time.time()

                for attempt in range(1, attempts + 1):
                    if attempts > 1:
                        if attempt > 1:
                            log(
                                "log",
                                {
                                    "step": idx,
                                    "line": f"retry {attempt}/{attempts} after failure…",
                                },
                                bus=bus,
                            )
                    rc, logfile = self._run_one(step, idx, run_dir, logs_dir, timeout_s, bus)
                    if rc == 0:
                        break

                elapsed = round(time.time() - t0_step, 3)
                log(
                    "action_done",
                    {
                        "step": idx,
                        "rc": rc,
                        "seconds": elapsed,
                        "log": str(logfile) if logfile else None,
                    },
                    bus=bus,
                )
                log(
                    "progress",
                    {"current": idx, "total": len(steps), "eta": None},
                    bus=bus,
                )

                if rc != 0 and not allow_fail:
                    log("run_finished", {"result": "FAILED"}, bus=bus)
                    print(f"[agent] run={run_id} result=FAILED")
                    print(f"[agent] events: {run_dir / 'events.jsonl'}")
                    print(f"[agent] logs:   {logs_dir}")
                    return 1

        except KeyboardInterrupt:
            # Graceful abort
            log("log", {"step": 0, "line": "KeyboardInterrupt: aborting run"}, bus=bus)
            log("run_finished", {"result": "ABORTED"}, bus=bus)
            print(f"[agent] run={run_id} result=ABORTED")
            print(f"[agent] events: {run_dir / 'events.jsonl'}")
            print(f"[agent] logs:   {logs_dir}")
            return 130

        log("run_finished", {"result": "OK"}, bus=bus)
        print(f"[agent] run={run_id} result=OK")
        print(f"[agent] events: {run_dir / 'events.jsonl'}")
        print(f"[agent] logs:   {logs_dir}")
        return 0

    # ---- helpers -------------------------------------------------------------

    def _run_one(
        self,
        step: Step,
        idx: int,
        run_dir: Path,
        logs_dir: Path,
        timeout_s: float | None,
        bus: EventBus,
    ) -> tuple[int, Path | None]:
        """
        Execute a single step once; return (rc, logfile_path_or_None).
        Supports timeouts for long-running exec/git commands.
        """
        rc = 0
        logfile: Path | None = None
        t_start = time.time()

        try:
            if step.op == "exec" and step.cmd:
                rc, logfile = self._run_streaming_cmd(
                    idx, step.cmd, run_dir, logs_dir, timeout_s, bus
                )

            elif step.op == "git" and step.args:
                cmd = " ".join(["git"] + step.args)
                rc, logfile = self._run_streaming_cmd(idx, cmd, run_dir, logs_dir, timeout_s, bus)

            elif step.op == "write" and step.path is not None and step.content is not None:
                write_file(Path(step.path), step.content, cwd=run_dir)

            elif (
                step.op == "patch"
                and step.path
                and (step.before is not None)
                and (step.after is not None)
            ):
                patch_file(Path(step.path), step.before, step.after, cwd=run_dir)

            elif step.op == "edit" and step.edits:
                apply_structured_edits(step.edits, cwd=run_dir)

            elif step.op == "scaffold" and step.layout:
                scaffold_layout(step.layout, cwd=run_dir)

            elif step.op == "py" and step.code is not None:
                locs: dict = {}
                try:
                    exec(step.code, {}, locs)  # noqa: S102
                    log(
                        "log",
                        {
                            "step": idx,
                            "line": f"py: executed, locals={list(locs.keys())}",
                        },
                        bus=bus,
                    )
                except Exception as e:  # noqa: BLE001
                    rc = 1
                    log("log", {"step": idx, "line": f"py error: {e}"}, bus=bus)

            elif step.op == "fetch" and getattr(step, "url", None) and getattr(step, "dest", None):
                dest = fetch_file(step.url, Path(step.dest))
                log("log", {"step": idx, "line": f"fetched -> {dest}"}, bus=bus)

            else:
                rc = 1
                log(
                    "log",
                    {"step": idx, "line": f"unknown or malformed step: {step.op}"},
                    bus=bus,
                )

        except KeyboardInterrupt:
            raise  # handled by outer try/except
        except Exception as e:  # noqa: BLE001
            rc = 1
            log("log", {"step": idx, "line": f"exception: {e}"}, bus=bus)

        # Timeout bookkeeping (for non-streaming ops we just check elapsed)
        if timeout_s and (time.time() - t_start) > timeout_s and rc == 0:
            rc = 1
            log("log", {"step": idx, "line": f"timeout exceeded: {timeout_s}s"}, bus=bus)

        return rc, logfile

    def _run_streaming_cmd(
        self,
        idx: int,
        cmd: str,
        run_dir: Path,
        logs_dir: Path,
        timeout_s: float | None,
        bus: EventBus,
    ) -> tuple[int, Path | None]:
        """
        Start a subprocess and stream lines to events and a log file.
        Enforces an optional timeout by killing the process if exceeded.
        """
        proc = run_stream(cmd, cwd=run_dir, env_add={}, safe_mode=self.safe_mode)
        logfile = logs_dir / f"step_{idx}.log"
        deadline = (time.time() + timeout_s) if timeout_s else None

        try:
            with logfile.open("w", encoding="utf-8") as lf:
                # Use readline loop so we can periodically check timeout
                while True:
                    line = proc.stdout.readline() if proc.stdout else ""
                    if line:
                        line = line.rstrip("\n")
                        lf.write(line + "\n")
                        log("log", {"step": idx, "line": line}, bus=bus)
                    else:
                        # no line available; check if process ended
                        if proc.poll() is not None:
                            break
                        # still running; check timeout and sleep briefly
                        if deadline and time.time() > deadline:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                            log(
                                "log",
                                {
                                    "step": idx,
                                    "line": f"timeout: killed process after {timeout_s}s",
                                },
                                bus=bus,
                            )
                            return 1, logfile
                        time.sleep(0.05)
        except KeyboardInterrupt:
            try:
                proc.kill()
            except Exception:
                pass
            raise
        except Exception as e:  # noqa: BLE001
            try:
                proc.kill()
            except Exception:
                pass
            log("log", {"step": idx, "line": f"stream error: {e}"}, bus=bus)
            return 1, logfile

        rc = proc.wait()
        return rc, logfile
