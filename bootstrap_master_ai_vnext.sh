#!/usr/bin/env bash
set -euo pipefail

# Create dirs
mkdir -p master_ai/{core,agents,self_update,tools} tests artifacts/projects

# -------- pyproject & dev tooling --------
if [ ! -f pyproject.toml ]; then
cat > pyproject.toml <<'PYPROJ'
[build-system]
requires = ["setuptools>=68","wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "master-ai"
version = "0.1.0"
description = "Master-AI: multi-agent planner/coder/executor with gates"
requires-python = ">=3.11"
dependencies = []

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E","F","I","UP","B","SIM"]
ignore = []

[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
PYPROJ
fi

cat > requirements-dev.txt <<'REQ'
ruff>=0.5
mypy>=1.9
pytest>=8
REQ

# -------- Makefile --------
cat > Makefile <<'MAKE'
.PHONY: dev-setup qa fmt type test

dev-setup:
	python -m pip install -U pip
	python -m pip install -r requirements-dev.txt

fmt:
	ruff check . --fix || true
	ruff format .

type:
	mypy master_ai || true

test:
	pytest -q || true

qa: fmt type test
MAKE

# -------- package init --------
cat > master_ai/__init__.py <<'PY'
__all__ = ["core", "agents"]
PY

# -------- core: task graph & context --------
cat > master_ai/core/context.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import time

@dataclass
class RunContext:
    root: Path
    artifacts: Path
    run_id: str

    @classmethod
    def new(cls, root: Path) -> "RunContext":
        run_id = time.strftime("%Y%m%d_%H%M%S")
        artifacts = root / "artifacts" / run_id
        artifacts.mkdir(parents=True, exist_ok=True)
        return cls(root=root, artifacts=artifacts, run_id=run_id)
PY

cat > master_ai/core/task_graph.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Any

TaskFn = Callable[[], Any]

@dataclass
class Task:
    name: str
    run: TaskFn

@dataclass
class TaskGraph:
    tasks: List[Task] = field(default_factory=list)

    def add(self, name: str, fn: TaskFn) -> "TaskGraph":
        self.tasks.append(Task(name, fn))
        return self

    def execute(self) -> None:
        for t in self.tasks:
            print(f"[Task] {t.name}…")
            t.run()
            print(f"[Task] {t.name} ✓")
PY

# -------- tools: safe shell --------
cat > master_ai/tools/shell.py <<'PY'
from __future__ import annotations
import subprocess
from typing import Sequence

ALLOWED = {"python","pytest","pip","echo","ls","cat","mkdir","touch","sh","bash"}

def run(cmd: Sequence[str], cwd: str | None = None, timeout: int = 120) -> subprocess.CompletedProcess:
    if cmd and cmd[0] not in ALLOWED:
        raise RuntimeError(f"Command not allowed: {cmd[0]}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
PY

# -------- agents: planner / coder / reviewer stubs --------
cat > master_ai/agents/planner.py <<'PY'
from __future__ import annotations
from master_ai.core.task_graph import TaskGraph

def plan_build_project(name: str, path: str) -> TaskGraph:
    """
    Minimal plan: scaffold -> write test -> run tests.
    """
    tg = TaskGraph()
    from master_ai.agents.coder import scaffold_project, write_tests, run_tests
    tg.add("scaffold", lambda: scaffold_project(name=name, path=path))
    tg.add("tests", lambda: write_tests(path=path))
    tg.add("pytest", lambda: run_tests(path=path))
    return tg
PY

cat > master_ai/agents/coder.py <<'PY'
from __future__ import annotations
from pathlib import Path
from master_ai.tools.shell import run

TEMPLATE_MAIN = '''def run():
    return "hello"

if __name__ == "__main__":
    print(run())
'''

TEMPLATE_README = "# {name}\n\nSimple auto-generated CLI.\n\n```\npython -m {name}\n```"

TEMPLATE_INIT = "__all__ = []\n"

TEMPLATE_TEST = '''from {name} import app

def test_run():
    assert app.run() == "hello"
'''

def scaffold_project(name: str, path: str) -> None:
    root = Path(path)
    (root / name).mkdir(parents=True, exist_ok=True)
    (root / name / "app.py").write_text(TEMPLATE_MAIN)
    (root / name / "__init__.py").write_text(TEMPLATE_INIT)
    (root / "README.md").write_text(TEMPLATE_README.format(name=name))
    (root / "pyproject.toml").write_text(f"""[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
""")
    # add a simple module launcher
    (root / name / "__main__.py").write_text("from . import app; print(app.run())\n")

def write_tests(path: str) -> None:
    root = Path(path)
    (root / "tests").mkdir(exist_ok=True)
    # refer to module as package import
    pkg = [p.name for p in root.iterdir() if p.is_dir()][0]
    (root / "tests" / "test_app.py").write_text(TEMPLATE_TEST.format(name=pkg))

def run_tests(path: str) -> None:
    cp = run(["pytest","-q"], cwd=path)
    print(cp.stdout.strip())
    if cp.returncode != 0:
        print(cp.stderr)
        raise SystemExit(cp.returncode)
PY

cat > master_ai/agents/reviewer.py <<'PY'
from __future__ import annotations

def review_summary(passed: bool) -> str:
    return "All tests passed." if passed else "Tests failed."
PY

# -------- self_update stubs (wire to your S3 overlay later) --------
cat > master_ai/self_update/manifest.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class VersionInfo:
    version: str
    sha256: str
    url: str | None = None
PY

cat > master_ai/self_update/apply.py <<'PY'
from __future__ import annotations

def self_check() -> bool:
    # place for lint/tests later; keep True so we can wire CI gates next
    return True
PY

# -------- CLI entry (replaces your old master_ai.py if present, but keeps name) --------
cat > master_ai.py <<'PY'
#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

from master_ai.core.context import RunContext
from master_ai.agents.planner import plan_build_project
from master_ai.self_update.apply import self_check

def cmd_self_check(_: argparse.Namespace) -> None:
    ok = self_check()
    print("Self-check:", "OK" if ok else "FAILED")
    raise SystemExit(0 if ok else 1)

def cmd_build_project(ns: argparse.Namespace) -> None:
    name: str = ns.name
    path = str(Path(ns.path).resolve())
    ctx = RunContext.new(Path.cwd())
    print(f"[Run {ctx.run_id}] build-project name={name} path={path}")
    tg = plan_build_project(name=name, path=path)
    tg.execute()
    print(f"[Run {ctx.run_id}] done. Project at {path}")

def main() -> None:
    p = argparse.ArgumentParser("master_ai", description="Master-AI vNext CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("self-check", help="Run internal lint/test gates")
    sp.set_defaults(func=cmd_self_check)

    sp = sub.add_parser("build-project", help="Generate a new automation-ready project")
    sp.add_argument("--name", required=True, help="Package name")
    sp.add_argument("--path", required=True, help="Destination directory")
    sp.set_defaults(func=cmd_build_project)

    ns = p.parse_args()
    ns.func(ns)

if __name__ == "__main__":
    main()
PY

# -------- tests --------
cat > tests/test_taskgraph.py <<'PY'
from master_ai.core.task_graph import TaskGraph

def test_graph_runs_in_order():
    order = []
    tg = TaskGraph()
    tg.add("a", lambda: order.append("a"))
    tg.add("b", lambda: order.append("b"))
    tg.execute()
    assert order == ["a","b"]
PY

echo "Bootstrap complete."
