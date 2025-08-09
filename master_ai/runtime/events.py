from __future__ import annotations

from pathlib import Path
import json
import time

ISO = "%Y-%m-%dT%H:%M:%S%z"


class EventBus:
    """Append-only JSONL event log for a single run directory."""
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.run_dir / "events.jsonl"
        if not self.path.exists():
            self.path.write_text("")

    def emit(self, kind: str, data: dict) -> None:
        evt = {"ts": time.strftime(ISO, time.gmtime()), "kind": kind, "data": data}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")


# --- module-level function expected by callers ---
def log(kind: str, data: dict, *, bus: "EventBus" = None) -> None:
    """Log an event; if no bus provided, silently ignore."""
    try:
        if bus:
            bus.emit(kind, data)
    except Exception:
        pass


# ---- Helpers used by the Streamlit monitor ----
def read_events(p: Path) -> list[dict]:
    path = p if str(p).endswith(".jsonl") else (Path(p) / "events.jsonl")
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                # skip broken lines
                pass
    return out


def latest_info(run_dir: Path) -> dict:
    info = {
        "result": None,
        "current": 0,
        "total": 0,
        "eta": None,
        "run_id": Path(run_dir).name,
        "goal": None,
        "safe": None,
        "started": None,
        "finished": None
    }
    for e in read_events(Path(run_dir)):
        k, d = e.get("kind"), e.get("data", {})
        if k == "run_started":
            info["goal"] = d.get("goal")
            info["safe"] = d.get("safe")
            info["started"] = e.get("ts")
        elif k == "plan_ready":
            info["total"] = len(d.get("steps") or [])
        elif k == "progress":
            info["current"] = d.get("current", info["current"])
            info["total"] = d.get("total", info["total"]) or info["total"]
        elif k == "run_finished":
            info["result"] = d.get("result")
            info["finished"] = e.get("ts")
    return info
