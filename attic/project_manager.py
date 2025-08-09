import json
import pathlib
import time

BASE = pathlib.Path.home() / "automation" / "projects"
BASE.mkdir(parents=True, exist_ok=True)


def ensure(project):
    path = BASE / project
    path.mkdir(exist_ok=True)
    for f in ("chat_history.json", "credentials.json"):
        p = path / f
        if not p.exists():
            p.write_text("{}")
    return path


def _load(p):
    return json.loads(open(p).read())


def _save(p, d):
    json.dump(d, open(p, "w"), indent=2)


def log(project, role, content):
    pj = ensure(project)
    f = pj / "chat_history.json"
    data = _load(f)
    data.setdefault("dialog", []).append({"t": time.time(), "role": role, "content": content})
    _save(f, data)


def last_msgs(project, n=10):
    f = ensure(project) / "chat_history.json"
    return _load(f).get("dialog", [])[-n:]
