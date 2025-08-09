from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shlex
import re
from typing import Any

@dataclass
class Step:
    op: str
    desc: str
    # generic fields (only a subset is used per op)
    cmd: str | None = None
    path: str | None = None
    content: str | None = None
    before: str | None = None
    after: str | None = None
    code: str | None = None
    edits: list[dict] | None = None
    layout: dict | None = None
    # extra fields for specialized ops
    url: str | None = None
    dest: str | None = None
    args: list[str] | None = None
    repo: str | None = None
    # controls
    retries: int = 0
    allow_fail: bool = False
    timeout: int | None = None  # seconds (only used where supported)

def _strip(s: str) -> str:
    return s.strip()

def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in blob.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out

def _json_or_text(s: str) -> Any:
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        return s

def _load_taskfile(path: Path) -> list[Any]:
    """
    Load a taskfile. Supported:
      - JSON list of strings: ["fetch: ...", "py: ...", ...]
      - JSON list of dicts:   [{"goal":"...", "retries":1, "allow_fail":true, "timeout":30}, ...]
      - JSON object with "steps": same as above
      - YAML with the same shapes (requires PyYAML)
    Returns a list of entries (str or dict with 'goal').
    """
    text = path.read_text(encoding="utf-8")

    def _extract(obj: Any) -> list[Any]:
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict) and "steps" in obj:
            steps = obj["steps"]
            return steps if isinstance(steps, list) else []
        return []

    # Try JSON
    try:
        data = json.loads(text)
        items = _extract(data)
    except Exception:
        # Try YAML if extension suggests it
        if path.suffix.lower() in {".yml", ".yaml"}:
            try:
                import yaml  # type: ignore
                data = yaml.safe_load(text)  # type: ignore
                items = _extract(data)
            except Exception as e:  # pragma: no cover
                raise ValueError(
                    f"taskfile: failed to parse YAML. Install PyYAML or use JSON. ({e})"
                ) from e
        else:
            raise ValueError("taskfile: not valid JSON (and not YAML by extension)")

    if not items:
        raise ValueError("taskfile: no steps/goals found")
    return items

def _apply_meta(steps: list[Step], meta: dict[str, Any]) -> list[Step]:
    r = int(meta.get("retries", 0) or 0)
    a = bool(meta.get("allow_fail", False))
    t = meta.get("timeout")
    t_int = int(t) if (t is not None and str(t).isdigit()) else None
    for s in steps:
        s.retries = r
        s.allow_fail = a
        s.timeout = t_int
    return steps

def _steps_for_goal(goal: str) -> list[Step]:
    g = goal.strip()

    # run: <shell>
    if g.startswith("run:"):
        cmd = g[len("run:"):].strip()
        return [Step(op="exec", desc=f"run shell: {cmd}", cmd=cmd)]

    # py: <code>
    if g.startswith("py:"):
        code = g[len("py:"):].lstrip("\n")
        return [Step(op="py", desc="run python snippet", code=code)]

    # write: path --- content
    if g.startswith("write:"):
        rest = g[len("write:"):].strip()
        if "---" not in rest:
            raise ValueError("write: needs 'path --- content'")
        path, content = map(_strip, rest.split("---", 1))
        return [Step(op="write", desc=f"write file {path}", path=path, content=content)]

    # patch: path --- before --- after
    if g.startswith("patch:"):
        rest = g[len("patch:"):].strip()
        parts = [p.strip() for p in rest.split("---")]
        if len(parts) != 3:
            raise ValueError("patch: needs 'path --- before --- after'")
        path, before, after = parts
        return [Step(op="patch", desc=f"patch {path}", path=path, before=before, after=after)]

    # edit: structured edits
    if g.startswith("edit:"):
        payload = g[len("edit:"):].strip()
        if payload.startswith("["):
            edits = json.loads(payload)
        else:
            d = _parse_kv_blob(payload.replace("\n", " "))
            edit = {k: d.get(k) for k in ("path", "op", "anchor", "text")}
            edits = [edit]
        return [Step(op="edit", desc="apply structured edits", edits=edits)]

    # scaffold: {"dirs":[...],"files":{...}}
    if g.startswith("scaffold:"):
        payload = g[len("scaffold:"):].strip()
        layout = _json_or_text(payload)
        if not isinstance(layout, dict):
            raise ValueError("scaffold: payload must be a JSON object with 'dirs'/'files'")
        return [Step(op="scaffold", desc="scaffold project layout", layout=layout)]

    # fetch: url=...; dest=...  OR  fetch: URL -> DEST
    if g.startswith("fetch:"):
        payload = g[len("fetch:"):].strip()
        m = re.match(r"^(?P<url>\S+)\s*->\s*(?P<dest>\S+)$", payload)
        if m:
            url = m.group("url")
            dest = m.group("dest")
            return [Step(op="fetch", desc=f"download {url} -> {dest}", url=url, dest=dest)]
        kv = _parse_kv_blob(payload)
        url, dest = kv.get("url"), kv.get("dest")
        if not url or not dest:
            raise ValueError("fetch: needs url=...; dest=...")
        return [Step(op="fetch", desc=f"download {url} -> {dest}", url=url, dest=dest)]

    # pip: <args...>
    if g.startswith("pip:"):
        args = shlex.split(g[len("pip:"):].strip())
        if not args:
            raise ValueError("pip: needs arguments, e.g. 'pip: install requests'")
        return [Step(op="pip", desc=f"pip {' '.join(args)}", args=args)]

    # git: clone URL -> DIR  OR raw args
    if g.startswith("git:"):
        payload = g[len("git:"):].strip()
        m = re.match(r"^clone\s+(?P<url>\S+)\s*->\s*(?P<dest>\S+)$", payload)
        if m:
            url = m.group("url")
            dest = m.group("dest")
            return [Step(op="git", desc=f"git clone {url} {dest}", args=["clone", url, dest])]
        args = shlex.split(payload)
        if not args:
            raise ValueError("git: needs arguments, e.g. 'git: clone https://... -> repo_dir'")
        return [Step(op="git", desc=f"git {' '.join(args)}", args=args)]

    # taskfile: handled by caller
    if g.startswith("taskfile:"):
        raise ValueError("taskfile: must be processed at a higher level")

    # fallback => shell
    return [Step(op="exec", desc=f"run shell: {g}", cmd=g)]

def make_plan(goal: str) -> list[Step]:
    g = goal.strip()

    if g.startswith("taskfile:"):
        payload = g[len("taskfile:"):].strip()
        d = _parse_kv_blob(payload.replace("\n", " "))
        raw_path = d.get("path")
        if not raw_path:
            raise ValueError("taskfile: needs path=...")
        items = _load_taskfile(Path(raw_path))
        steps: list[Step] = []
        for item in items:
            if isinstance(item, str):
                steps.extend(_steps_for_goal(item))
            elif isinstance(item, dict) and "goal" in item and isinstance(item["goal"], str):
                meta = {k: item.get(k) for k in ("retries", "allow_fail", "timeout")}
                s = _steps_for_goal(item["goal"])
                steps.extend(_apply_meta(s, meta))
        if not steps:
            raise ValueError("taskfile: produced no executable steps")
        return steps

    return _steps_for_goal(g)
