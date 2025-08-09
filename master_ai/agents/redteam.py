from __future__ import annotations

import re

SUS_PATTERNS = [
    r"(?i)rm\s+-rf\s+/",
    r"(?i)curl\s+.*\|\s*sh",
    r"(?i)aws\s+secretsmanager",
    r"(?i)gcloud\s+secrets",
]


def scan(text: str) -> list[str]:
    hits = []
    for pat in SUS_PATTERNS:
        if re.search(pat, text):
            hits.append(pat)
    return hits
