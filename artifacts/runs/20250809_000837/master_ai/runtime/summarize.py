from __future__ import annotations
import re
from html import unescape

def summarize_text(txt: str, max_lines: int = 5) -> str:
    """
    Return the first `max_lines` of text with basic cleanup.
    Never returns None.
    """
    if txt is None:
        return ""
    # very naive HTML strip in case we got a page
    s = re.sub(r"<[^>]+>", " ", txt)
    s = unescape(s)
    # collapse whitespace per line, drop empties
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    return "\n".join(lines[:max_lines])

def summarize_url(url: str, max_lines: int = 5) -> str:
    from .net import fetch_text
    return summarize_text(fetch_text(url), max_lines)