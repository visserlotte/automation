from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Finding:
    source: str
    summary: str


def gather_context(goal: str) -> list[Finding]:
    # Offline stub: later wire to web or local KB.
    return [
        Finding(source="local", summary=f"No external research; working offline for goal: {goal}")
    ]
