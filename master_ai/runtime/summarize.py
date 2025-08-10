from __future__ import annotations

import re
from html import unescape

# --- tiny HTML scrubber ------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\f\r\v]+")


def _strip_html(s: str) -> str:
    # remove tags, unescape entities, normalize spaces
    s = _TAG_RE.sub(" ", s)
    s = unescape(s)
    # collapse intra-line whitespace
    s = _WS_RE.sub(" ", s)
    return s


# --- public API --------------------------------------------------------------


def summarize_text(txt: str | bytes | None, max_lines: int = 5) -> str:
    """
    Take raw text or HTML and return the first `max_lines` of cleaned text.
    Never returns None.
    """
    if txt is None:
        return ""
    if isinstance(txt, bytes):
        try:
            txt = txt.decode("utf-8", errors="ignore")
        except Exception:
            txt = txt.decode("latin-1", errors="ignore")

    s = _strip_html(str(txt))
    # per-line trim, drop empty, return first N
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    if not lines:
        # fallback: split on periods if page had no newlines
        chunks = [c.strip() for c in re.split(r"[\.!?]+", s) if c.strip()]
        lines = chunks
    return "\n".join(lines[:max_lines])


def summarize_url(url: str, max_lines: int = 5) -> str:
    """
    Fetch a URL using runtime.net.fetch_text, then summarize it.
    """
    from .net import fetch_text

    text = fetch_text(url)
    return summarize_text(text, max_lines)


def summarize_file(path: str | bytes, max_lines: int = 5, encoding: str = "utf-8") -> str:
    """
    Read a file from disk and summarize its contents.
    """
    from pathlib import Path

    p = Path(path)
    data = p.read_text(encoding=encoding, errors="ignore")
    return summarize_text(data, max_lines)
