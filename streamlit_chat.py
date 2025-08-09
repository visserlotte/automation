#!/usr/bin/env python3
"""
Streamlit chat for MasterAI — smooth log updates
------------------------------------------------
  ▸ ##status##   – latest self-edit timestamp
  ▸ /run …       – launch master_ai build loop
Logs are tailed by a background thread which triggers st.rerun()
only when the file changes → no page flashing.
History lives in ./chat_history/<session>.json
"""

from __future__ import annotations

import datetime
import glob
import importlib
import json
import os
import pathlib
import threading
import time
import uuid

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parent
LOG_FILE = ROOT / "logs" / "current_run.log"
HIST_DIR = ROOT / "chat_history"
HIST_DIR.mkdir(exist_ok=True)


# ──── helpers ──────────────────────────────────────────────────────────────
def _hist_path(sid: str) -> pathlib.Path:
    return HIST_DIR / f"{sid}.json"


def _save_history() -> None:
    if "sid" in st.session_state and "messages" in st.session_state:
        _hist_path(st.session_state.sid).write_text(json.dumps(st.session_state.messages, indent=2))


def _load_history(sid: str) -> list[dict]:
    p = _hist_path(sid)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return []


def master_ai_chat(prompt: str) -> str:
    """Dispatch prompt to built-ins or master_ai.gpt_chat()."""
    lower = prompt.strip().lower()
    if lower == "##status##":
        plans = sorted(glob.glob("plans/plan_*.txt"), key=os.path.getmtime, reverse=True)
        if plans:
            ts = datetime.datetime.fromtimestamp(os.path.getmtime(plans[0])).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            return f"Latest micro-project: {os.path.basename(plans[0])} (edited {ts})"
        return "No recorded self-edits yet."
    if lower.startswith("/run ") and len(prompt.strip()) > 10:
        from ai_helpers.run_goal import run_goal_async

        return run_goal_async(prompt[5:].strip())
    try:
        master_ai = importlib.import_module("master_ai")
        resp = master_ai.gpt_chat(prompt)
        return resp.get("result", "(empty)")
    except Exception as e:
        return f"⚠️ error: {e}"


def add_msg(role: str, content: str) -> None:
    st.session_state.messages.append({"id": str(uuid.uuid4()), "role": role, "content": content})
    _save_history()


# ──── background log-tail thread ───────────────────────────────────────────
def _tail_log() -> None:
    last_size = 0
    while True:
        try:
            size = LOG_FILE.stat().st_size
            if size != last_size:
                last_size = size
                lines = LOG_FILE.read_text().splitlines()[-20:]
                st.session_state._log_tail = "\n".join(lines) if lines else "(idle)"
                if hasattr(st, "rerun"):
                    st.rerun()
            time.sleep(2)
        except Exception:
            time.sleep(2)


if "_log_thread" not in st.session_state:
    st.session_state._log_tail = "(idle)"
    t = threading.Thread(target=_tail_log, daemon=True)
    t.start()
    st.session_state._log_thread = t

# ──── page config / state ─────────────────────────────────────────────────
st.set_page_config(page_title="MasterAI Chat", layout="wide")

if "sid" not in st.session_state:
    st.session_state.sid = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
if "messages" not in st.session_state:
    st.session_state.messages = _load_history(st.session_state.sid)

left, main, right = st.columns([2, 6, 2])

with left:
    st.header("Conversations")
    st.write("📂 (folders coming soon)")
    st.divider()

with main:
    st.header("💬 Chat")
    for m in st.session_state.messages:
        align = "right" if m["role"] == "user" else "left"
        colour = "#0078d4" if m["role"] == "user" else "#2d2d2d"
        st.markdown(
            f"<div style='text-align:{align}; margin:4px 0;'>"
            f"  <span style='display:inline-block; max-width:80%;"
            f"               background:{colour}; color:white;"
            f"               padding:8px 12px; border-radius:8px;'>"
            f"    {m['content']}"
            f"  </span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    prompt = st.text_input("Message", key="user_in", label_visibility="collapsed")
    if st.button("Send", type="primary") and prompt.strip():
        add_msg("user", prompt)
        with st.spinner("MasterAI is thinking…"):
            reply = master_ai_chat(prompt)
        add_msg("assistant", reply)
        if hasattr(st, "rerun"):
            st.rerun()

with right:
    st.header("🧠 Thoughts / Doing")
    st.code(st.session_state._log_tail, language="bash")

# open browser locally
if os.getenv("STREAMLIT_AUTOLAUNCH"):
    import threading as _th
    import webbrowser

    _th.Timer(1.0, lambda: webbrowser.open("http://localhost:8501")).start()
