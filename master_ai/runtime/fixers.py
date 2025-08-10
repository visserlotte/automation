from __future__ import annotations

import re
from pathlib import Path

# Optional event logger: if unavailable, no-op
try:
    from .events import log as _emit  # type: ignore
except Exception:  # pragma: no cover

    def _emit(*_a, **_k):  # noqa: D401 - tiny shim
        pass


# Resolve repo root from this file location: …/master_ai/runtime/fixers.py
# parents[0]=runtime, [1]=master_ai, [2]=repo root
PROJ_ROOT = Path(__file__).resolve().parents[2]

# Patterns we know how to repair
_MISSING_IMPORT_PATTERNS = [
    # e.g. "cannot import name 'missing_fn' from 'master_ai.dummy' (/path/master_ai/dummy.py)"
    re.compile(
        r"cannot import name ['\"](?P<name>[^'\"]+)['\"] from ['\"](?P<mod>master_ai[\w\.]*)['\"](?: \((?P<file>[^)]+)\))?",
        re.IGNORECASE,
    ),
    # Sometimes Python says "from partially initialized module ..."
    re.compile(
        r"cannot import name ['\"](?P<name>[^'\"]+)['\"] from (?:partially initialized module )?['\"](?P<mod>master_ai[\w\.]*)['\"](?: \((?P<file>[^)]+)\))?",
        re.IGNORECASE,
    ),
]

# e.g. "No module named 'master_ai.does_not_exist'"
_NO_MODULE_PATTERNS = [
    re.compile(r"No module named ['\"](?P<mod>master_ai[\w\.]*)['\"]", re.IGNORECASE),
]


def _parse_missing_symbol(error_text: str) -> tuple[str, str] | None:
    """Extract (missing_name, module) when a symbol import fails."""
    for rx in _MISSING_IMPORT_PATTERNS:
        m = rx.search(error_text)
        if m:
            return m.group("name"), m.group("mod")
    return None


def _parse_missing_module(error_text: str) -> str | None:
    """Extract a missing module 'master_ai.xxx' when the module import fails."""
    for rx in _NO_MODULE_PATTERNS:
        m = rx.search(error_text)
        if m:
            return m.group("mod")
    return None


def _module_to_file(module: str) -> Path | None:
    """
    Convert 'master_ai.something' to repo file path, if inside our tree.
    Do NOT try to create 'master_ai.py' for the top-level package.
    """
    if not module.startswith("master_ai"):
        return None
    if module == "master_ai":
        return None
    return PROJ_ROOT / (module.replace(".", "/") + ".py")


def _ensure_module_file(module: str, *, bus=None) -> Path | None:
    """
    If a module file is missing inside our repo, create a minimal stub file.
    Returns the path if created or already exists; None if outside tree.
    """
    dst = _module_to_file(module)
    if dst is None:
        return None
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("# auto-created by fixers.py\n", encoding="utf-8")
        try:
            _emit(
                "log",
                {"step": 1, "line": f"fixer: created — module file {dst}"},
                bus=bus,
            )
        except Exception:
            pass
    return dst


def _classify_symbol(name: str) -> str:
    """
    Heuristics:
      - UPPER_SNAKE => const
      - PascalCase  => class
      - else        => function
    """
    if name.isupper():
        return "const"
    if re.match(r"[A-Z][A-Za-z0-9_]*$", name):
        return "class"
    return "func"


def _append_symbol_stub(dst: Path, symbol: str) -> bool:
    """
    Append a simple stub for the missing symbol.
      - function: def name(*_a, **_k): pass
      - class:    class Name: pass
      - const:    NAME = None
    Only patches existing project files.
    """
    if not dst.exists():
        return False

    try:
        text = dst.read_text(encoding="utf-8")
    except Exception:
        return False

    # If symbol already defined somewhere, bail
    if re.search(rf"^\s*def\s+{re.escape(symbol)}\s*\(", text, re.M):
        return False
    if re.search(rf"^\s*class\s+{re.escape(symbol)}\s*[\(:]", text, re.M):
        return False
    if re.search(rf"^\s*{re.escape(symbol)}\s*=", text, re.M):
        return False

    kind = _classify_symbol(symbol)
    if kind == "func":
        snippet = (
            f"\n\ndef {symbol}(*_a, **_k):\n"
            f'    """Auto-added shim by fixers.py (until real implementation exists)."""\n'
            f"    pass\n"
        )
    elif kind == "class":
        snippet = (
            f"\n\nclass {symbol}:\n"
            f'    """Auto-added shim by fixers.py (until real implementation exists)."""\n'
            f"    pass\n"
        )
    else:  # const
        snippet = f"\n\n{symbol} = None  # Auto-added shim by fixers.py (until real implementation exists).\n"

    try:
        dst.write_text(text + snippet, encoding="utf-8")
        return True
    except Exception:
        return False


def apply_import_fix(error_text: str, *, bus=None) -> bool:
    """
    Attempt to fix ImportError by either:
      1) Creating a missing module file; or
      2) Appending a stub for a missing symbol in a project module.

    Returns True if a change was made that might allow a retry; else False.
    """
    # Missing module case.
    mod = _parse_missing_module(error_text)
    if mod:
        path = _ensure_module_file(mod, bus=bus)
        if path is not None:
            try:
                _emit("log", {"step": 1, "line": "fixer: retrying after shim…"}, bus=bus)
            except Exception:
                pass
            return True

    # Missing symbol in an existing module.
    parsed = _parse_missing_symbol(error_text)
    if parsed:
        name, module = parsed
        dst = _ensure_module_file(module, bus=bus)  # ensure the module file exists
        if dst:
            ok = _append_symbol_stub(dst, name)
            line = f"fixer: {'patched' if ok else 'no-op'} — added shim for {name} in {dst}"
            try:
                _emit("log", {"step": 1, "line": line}, bus=bus)
                _emit("log", {"step": 1, "line": "fixer: retrying after shim…"}, bus=bus)
            except Exception:
                pass
            return ok

    return False
