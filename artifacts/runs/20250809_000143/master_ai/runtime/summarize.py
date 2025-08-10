from __future__ import annotations


def summarize_text(txt: str, max_lines: int = 5) -> str:
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    return "\n".join(lines[:max_lines])
