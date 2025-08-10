# ui/monitor.py
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import streamlit as st

# ---------- Config ----------
ROOT = Path.cwd()
RUNS_ROOT = ROOT / "artifacts" / "runs"
RUNS_ROOT.mkdir(parents=True, exist_ok=True)

PAGE_TITLE = "Master-AI — Run Monitor"
SIDEBAR_REFRESH_DEFAULT = 2  # seconds
RECENT_EVENTS_LIMIT = 12
STEP_LOG_MAX_BYTES = 64 * 1024  # 64 KB


# ---------- Helpers ----------
def list_runs(root: Path = RUNS_ROOT) -> list[Path]:
    runs = [p for p in root.iterdir() if p.is_dir()]
    runs.sort()
    return runs


def read_events(run_dir: Path) -> tuple[list[dict[str, Any]], float]:
    ev_path = run_dir / "events.jsonl"
    events: list[dict[str, Any]] = []
    if not ev_path.exists():
        return events, 0.0
    with ev_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                # Keep going if a partially-written line appears
                continue
    mtime = ev_path.stat().st_mtime
    return events, mtime


def extract_info(events: list[dict[str, Any]]) -> dict[str, Any]:
    info: dict[str, Any] = {
        "run_id": None,
        "goal": None,
        "safe": None,
        "started": None,
        "finished": None,
        "current": 0,
        "total": 0,
        "eta": None,
        "result": None,
        "step_log_path": None,
        "last_thought": None,
    }
    for ev in events:
        kind = ev.get("kind")
        data = ev.get("data", {})
        if kind == "run_started":
            info["run_id"] = data.get("run_id")
            info["goal"] = data.get("goal")
            info["safe"] = data.get("safe")
            info["started"] = ev.get("ts")
        elif kind == "progress":
            info["current"] = data.get("current") or 0
            info["total"] = data.get("total") or 0
            info["eta"] = data.get("eta")
        elif kind == "action_done":
            # if a log file path is provided, keep the latest
            if data.get("log"):
                info["step_log_path"] = data.get("log")
        elif kind == "thought":
            info["last_thought"] = data.get("text")
        elif kind == "run_finished":
            info["finished"] = ev.get("ts")
            info["result"] = data.get("result")
    return info


def tail_file(path: Path, max_bytes: int = STEP_LOG_MAX_BYTES) -> str:
    if not path.exists():
        return ""
    # Simple tail: read the end of file up to max_bytes
    size = path.stat().st_size
    with path.open("rb") as f:
        if size > max_bytes:
            f.seek(size - max_bytes)
            chunk = f.read()
            # try to avoid half-char/line issues
            text = chunk.decode(errors="replace")
            # Drop partial first line
            text = text.splitlines(True)
            if text and not text[0].endswith(("\n", "\r")):
                text = text[1:]
            return "".join(text)
        return f.read().decode(errors="replace")


def download_byteslabel(data: bytes, file_name: str, label: str):
    st.download_button(
        label=label,
        data=data,
        file_name=file_name,
        mime="application/octet-stream",
        use_container_width=False,
    )


def events_mtime(run_dir: Path) -> float:
    p = run_dir / "events.jsonl"
    return p.stat().st_mtime if p.exists() else 0.0


# ---------- UI ----------
st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title(PAGE_TITLE)

# Sidebar
with st.sidebar:
    st.subheader("Auto-refresh interval (seconds)")
    refresh_sec = st.slider(
        "seconds", min_value=0, max_value=10, value=SIDEBAR_REFRESH_DEFAULT, step=1
    )
    if st.button("Refresh now"):
        st.rerun()

    runs = list_runs()
    st.subheader("Run directory")
    if runs:
        # Default to the most recent run
        latest_name = runs[-1].name
        default_idx = len(runs) - 1
        sel = st.selectbox(
            "Pick a run", [p.name for p in runs], index=default_idx, key="run_select"
        )
        run_dir = RUNS_ROOT / sel
    else:
        st.info("No runs found under artifacts/runs")
        run_dir = RUNS_ROOT / "(none)"

# Read events + derive info
events, mtime = read_events(run_dir)
info = extract_info(events)

# Persist mtime/next refresh to minimize full-page re-renders
if "last_events_mtime" not in st.session_state:
    st.session_state["last_events_mtime"] = 0.0
if "next_refresh" not in st.session_state:
    st.session_state["next_refresh"] = 0.0

# Header metrics
cols = st.columns(5)
cols[0].metric("Run ID", info["run_id"] or "—")
cols[1].metric("Safe mode", "ON" if info["safe"] else "OFF" if info["safe"] is not None else "—")
cols[2].metric("Started", info["started"] or "—")
cols[3].metric("Finished", info["finished"] or "—")
cols[4].metric("Goal", info["goal"] or "—")

# Status banner
status_text = (
    f"Run finished: {info['result']}"
    if info["result"]
    else "Run in progress…"
    if info["total"]
    else "Waiting for steps…"
)
if info["result"] == "OK":
    st.success(status_text)
elif info["result"]:
    st.warning(status_text)
else:
    st.info(status_text)

# Progress + ETA
progress = min(1.0, info["current"] / max(1, info["total"])) if info["total"] else 0.0
st.progress(progress)
eta_text = info["eta"] or "n/a"
st.caption(f"🤖 ETA: {eta_text}")

# Thought (last reasoning message)
if info["last_thought"]:
    with st.expander("Agent thought (latest)", expanded=False):
        st.write(info["last_thought"])

st.divider()

left, right = st.columns([2, 1])

# Live step log
with left:
    st.subheader("Live step log")
    log_path = Path(info["step_log_path"]) if info.get("step_log_path") else None
    if log_path and log_path.exists():
        txt = tail_file(log_path)
        st.code(txt or "(log is empty)", language="bash")
        download_byteslabel(
            data=log_path.read_bytes(),
            file_name=log_path.name,
            label="Download step log",
        )
    else:
        st.caption("No step log yet.")

# Recent events
with right:
    st.subheader("Recent events")
    show = events[-RECENT_EVENTS_LIMIT:][::-1]  # newest first
    if not show:
        st.caption("No events yet.")
    else:
        for ev in show:
            st.json(ev, expanded=False)

# Raw events download
ev_file = run_dir / "events.jsonl"
if ev_file.exists():
    download_byteslabel(
        data=ev_file.read_bytes(), file_name=ev_file.name, label="Download events.jsonl"
    )

# ---------- Smart auto-rerun ----------
# Rerun if file changed OR timer elapsed
now = time.time()
changed = mtime > st.session_state["last_events_mtime"]
time_ok = refresh_sec and (now >= st.session_state["next_refresh"])

if changed or time_ok:
    st.session_state["last_events_mtime"] = mtime
    st.session_state["next_refresh"] = now + (refresh_sec or 0)
    # Avoid infinite loop if nothing is displayed yet
    if refresh_sec or changed:
        st.rerun()
