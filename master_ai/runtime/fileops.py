from __future__ import annotations
from pathlib import Path
from typing import Iterable

# Optional event logging shim (no-op if not available)
try:
    from .events import log as _emit  # type: ignore
except Exception:  # pragma: no cover
    def _emit(*_a, **_k):  # noqa: D401 - tiny shim
        pass

def _resolve(cwd: Path | str, p: Path | str) -> Path:
    base = Path(cwd)
    return (base / p).resolve() if not str(p).startswith("/") else Path(p)

def write_file(path: Path | str, content: str, *, cwd: Path | str) -> Path:
    """Create/overwrite file with content (mkdir parents)."""
    dst = _resolve(cwd, path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")
    _emit("log", {"step": 1, "line": f"write: {dst} ({len(content)} bytes)"})
    return dst

def patch_file(path: Path | str, before: str, after: str, *, cwd: Path | str) -> bool:
    """Simple string replace of first occurrence. Returns True if changed."""
    dst = _resolve(cwd, path)
    s = dst.read_text(encoding="utf-8")
    if before not in s:
        _emit("log", {"step": 1, "line": f"patch: pattern not found in {dst}"})
        return False
    s2 = s.replace(before, after, 1)
    if s2 != s:
        dst.write_text(s2, encoding="utf-8")
        _emit("log", {"step": 1, "line": f"patch: changed {dst}"})
        return True
    return False

# ---- Structured edits -------------------------------------------------------

def _insert_after(text: str, anchor: str, snippet: str) -> str:
    i = text.find(anchor)
    if i < 0:
        return text
    j = i + len(anchor)
    return text[:j] + snippet + text[j:]

def _insert_before(text: str, anchor: str, snippet: str) -> str:
    i = text.find(anchor)
    if i < 0:
        return text
    return text[:i] + snippet + text[i:]

def _replace(text: str, anchor: str, snippet: str) -> str:
    return text.replace(anchor, snippet)

def _delete_line_with(text: str, anchor: str) -> str:
    lines = text.splitlines(keepends=True)
    keep: list[str] = []
    for ln in lines:
        if anchor in ln:
            continue
        keep.append(ln)
    return "".join(keep)

def apply_structured_edits(edits: Iterable[dict], *, cwd: Path | str) -> None:
    """
    Apply a list of edit dicts. Each edit:
      {
        "path": "file",
        "op": <insert_after|insert_before|replace|delete_line|append|prepend>,
        "anchor": "...",
        "text": "..."
      }
    """
    for e in edits:
        dst = _resolve(cwd, e["path"])
        s = dst.read_text(encoding="utf-8") if dst.exists() else ""
        op = e["op"]
        if op == "insert_after":
            s = _insert_after(s, e["anchor"], e["text"])
        elif op == "insert_before":
            s = _insert_before(s, e["anchor"], e["text"])
        elif op == "replace":
            s = _replace(s, e["anchor"], e["text"])
        elif op == "delete_line":
            s = _delete_line_with(s, e["anchor"])
        elif op == "append":
            s += e["text"]
        elif op == "prepend":
            s = e["text"] + s
        else:
            raise ValueError(f"Unknown edit op: {op}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(s, encoding="utf-8")
        _emit("log", {"step": 1, "line": f"edit: {dst} op={op}"})

def scaffold_layout(paths: Iterable[str | Path], *, cwd: Path | str) -> None:
    """Create empty files/dirs as per given relative paths."""
    for rel in paths:
        dst = _resolve(cwd, rel)
        if str(rel).endswith("/"):
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                dst.write_text("", encoding="utf-8")
        _emit("log", {"step": 1, "line": f"scaffold: {dst}"})
