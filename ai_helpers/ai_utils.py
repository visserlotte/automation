# ai_utils.py

import json
import pathlib

from ai_helpers.master_ai_config import openai

chat_log_path = (
    lambda project: pathlib.Path.home() / "automation" / "projects" / project / "chat_history.json"
)


def last_msgs(project, n=10):
    f = chat_log_path(project)
    if f.exists():
        try:
            data = json.loads(f.read_text())
            return data[-n:] if isinstance(data, list) else []
        except Exception as e:
            print(f"🔧 last_msgs error: {e}")
    return []


SYSTEM_PROMPT = """You are Master-AI: Secure, precise, self-healing.
If you see any error, explain, log, and auto-repair.
Proactively research and suggest tools if asked."""


def gpt(prompt: str, history=None) -> str:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        msgs += history[-10:] if isinstance(history, list) else last_msgs(history)
    msgs.append({"role": "user", "content": prompt})
    try:
        r = openai.chat.completions.create(model="gpt-4o", messages=msgs)
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT error: {e}"


# === STATUS HOOK ===
from pathlib import Path


def _last_update() -> str:
    """Return human note of the most recent self-edit."""
    plans = sorted(Path("plans").glob("plan_*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if plans:
        return f"Latest micro-project: {plans[0].name} (edited {plans[0].stat().st_mtime:%Y-%m-%d %H:%M})"
    return "No edits recorded yet."
