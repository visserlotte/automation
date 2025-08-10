# ui/studio.py
from __future__ import annotations

import shlex
import subprocess
import time
from pathlib import Path

import streamlit as st

ROOT = Path.cwd()
RUNS_ROOT = ROOT / "artifacts" / "runs"
RUNS_ROOT.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Master-AI Studio", layout="wide")
st.title("🧠 Master-AI Studio")


# ---------- helpers ----------
def newest_run_dir() -> Path | None:
    if not RUNS_ROOT.exists():
        return None
    runs = [p for p in RUNS_ROOT.iterdir() if p.is_dir()]
    if not runs:
        return None
    return sorted(runs)[-1]


def run_cli(goal: str, unsafe: bool) -> tuple[int, str]:
    cmd = f"PYTHONPATH=. python -m master_ai agent-run --goal {shlex.quote(goal)}"
    if unsafe:
        cmd += " --unsafe"
    # We run in project root
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        shell=True,
        text=True,
        capture_output=True,
        executable="/bin/bash",
    )
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return proc.returncode, out


# ---------- sidebar ----------
with st.sidebar:
    st.subheader("Quick actions")
    if st.button("Plan (hello world)"):
        st.session_state["goal"] = "run: echo hello world"
    if st.button("Self-check"):
        st.session_state["goal"] = "run: python -m master_ai self-check"

    st.divider()
    st.caption("This launches `python -m master_ai agent-run` in your repo root.")
    st.caption("Unsafe mode lets the agent use full shell, not just allowlisted exec.")

# ---------- main ----------
default_goal = st.session_state.get("goal", "run: echo hello from studio")
goal = st.text_input(
    "Goal",
    value=default_goal,
    key="goal",
    placeholder="e.g. write: tmp/demo.txt --- hello world",
)

col1, col2 = st.columns([1, 1])
run_safe = col1.button("▶ Run (safe)", type="primary")
run_unsafe = col2.button("⚠ Run (unsafe)")

# Report last known newest run so user can inspect before launching
with st.expander("Last runs", expanded=False):
    runs = sorted([p for p in RUNS_ROOT.iterdir() if p.is_dir()])[-10:]
    if runs:
        for p in runs[::-1]:
            st.write(p.name)
    else:
        st.caption("(no runs yet)")

# Execute
if run_safe or run_unsafe:
    unsafe = bool(run_unsafe)
    st.write("Launching…")
    before = newest_run_dir()
    code, output = run_cli(goal, unsafe)
    after = newest_run_dir()
    st.subheader("CLI output")
    st.code(output.rstrip() or "(no output)", language="bash")

    # Find run id
    run_dir = None
    if after and (before is None or after != before):
        run_dir = after
    # Fallback: scan by time if not detectable
    if run_dir is None:
        run_dir = newest_run_dir()

    if code == 0:
        st.success("Launch OK.")
    else:
        st.error(f"Launch failed (rc={code}).")

    if run_dir:
        rid = run_dir.name
        st.subheader("Run artifacts")
        st.write(f"Run dir: `{run_dir}`")

        # Handy links (monitor expects to be on :8502 per your Makefile)
        monitor_url = f"http://{st.runtime.scriptrunner.get_script_run_ctx().session_info.client.request.headers.get('host', 'localhost').split(':')[0]}:8502"
        st.link_button("Open monitor", monitor_url, use_container_width=False)
        st.caption(f"(Select `{rid}` in the monitor’s run dropdown)")

    st.caption(time.strftime("Launched at %Y-%m-%d %H:%M:%S"))

st.divider()
st.markdown("#### Tips")
st.markdown(
    """
- **Examples**
  - `run: echo hi`
  - `write: tmp/demo.txt --- hello world`
  - `patch: tmp/demo.txt --- hello --- hola`
  - `py: x=2+2; open('tmp/num.txt','w').write(str(x))`
- Use **unsafe** when you want full `/bin/bash` (the agent will not restrict commands).
"""
)
