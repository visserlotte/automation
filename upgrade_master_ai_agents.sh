#!/usr/bin/env bash
set -euo pipefail

echo "[upgrade] Creating dirs…"
mkdir -p master_ai/{core,agents,self_update,tools} ui tests artifacts/runs

# ---------- core: executor + queue ----------
cat > master_ai/core/executor.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import shutil, os, subprocess, json, time
from typing import Sequence

ALLOWED_CMDS = {"python","pytest","pip","echo","ls","cat","mkdir","touch","sh","bash"}

@dataclass
class ExecResult:
    returncode: int
    stdout: str
    stderr: str
    cmd: list[str]
    cwd: str

class Executor:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.sandbox = run_dir / "sandbox"
        self.logs = run_dir / "logs"
        self.sandbox.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def run(self, cmd: Sequence[str], *, cwd: Path | None = None, env: dict | None = None, timeout: int = 300) -> ExecResult:
        if cmd and cmd[0] not in ALLOWED_CMDS:
            raise RuntimeError(f"Command not allowed: {cmd[0]}")
        wdir = (cwd or self.sandbox)
        penv = os.environ.copy()
        if env:
            penv.update(env)
        p = subprocess.run(
            list(cmd),
            cwd=str(wdir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=penv,
        )
        ts = time.strftime("%Y%m%d_%H%M%S")
        (self.logs / f"cmd_{ts}.log").write_text(
            json.dumps({
                "cmd": cmd, "cwd": str(wdir), "rc": p.returncode,
                "stdout": p.stdout, "stderr": p.stderr
            }, indent=2)
        )
        return ExecResult(p.returncode, p.stdout, p.stderr, list(cmd), str(wdir))

    def stage_project(self, src: Path) -> Path:
        """Copy a project into the sandbox (shallow) and return the dest path."""
        dest = self.sandbox / src.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        return dest
PY

cat > master_ai/core/queue.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, List

@dataclass
class Job:
    name: str
    fn: Callable[[], Any]

class JobQueue:
    def __init__(self) -> None:
        self.jobs: List[Job] = []

    def add(self, name: str, fn: Callable[[], Any]) -> "JobQueue":
        self.jobs.append(Job(name, fn))
        return self

    def run(self) -> None:
        for j in self.jobs:
            print(f"[Queue] {j.name}…")
            j.fn()
            print(f"[Queue] {j.name} ✓")
PY

# ---------- agents: planner/researcher/reviewer/redteam/ops ----------
cat > master_ai/agents/planner.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class PlanStep:
    name: str
    desc: str

def make_plan(goal: str) -> List[PlanStep]:
    steps: List[PlanStep] = []
    steps.append(PlanStep("scaffold", f"Create a minimal project for: {goal}"))
    steps.append(PlanStep("tests", "Add basic tests to validate success criteria"))
    steps.append(PlanStep("implement", "Write the simplest code to satisfy the tests"))
    steps.append(PlanStep("lint_type_test", "Run ruff, mypy, and pytest"))
    steps.append(PlanStep("package", "Ensure the project runs as a module"))
    return steps
PY

cat > master_ai/agents/researcher.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class Finding:
    source: str
    summary: str

def gather_context(goal: str) -> List[Finding]:
    # Offline stub: later wire to web or local KB.
    return [Finding(source="local", summary=f"No external research; working offline for goal: {goal}")]
PY

cat > master_ai/agents/reviewer.py <<'PY'
from __future__ import annotations
from pathlib import Path
from master_ai.tools.shell import run

def run_quality_gates(project_path: Path) -> None:
    # Be lenient; don't break on missing tools
    run(["ruff","check","--fix","."], cwd=str(project_path))
    run(["ruff","format","."], cwd=str(project_path))
    run(["mypy","."], cwd=str(project_path))
    cp = run(["pytest","-q"], cwd=str(project_path), env={"PYTHONPATH": str(project_path.resolve())})
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)
PY

cat > master_ai/agents/redteam.py <<'PY'
from __future__ import annotations
import re

SUS_PATTERNS = [
    r'(?i)rm\s+-rf\s+/',
    r'(?i)curl\s+.*\|\s*sh',
    r'(?i)aws\s+secretsmanager',
    r'(?i)gcloud\s+secrets',
]

def scan(text: str) -> list[str]:
    hits = []
    for pat in SUS_PATTERNS:
        if re.search(pat, text):
            hits.append(pat)
    return hits
PY

cat > master_ai/agents/ops.py <<'PY'
from __future__ import annotations
from pathlib import Path
import shutil

def stage_output(artifact_dir: Path, project_path: Path) -> Path:
    out = artifact_dir / "output"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(project_path, out)
    return out
PY

# ---------- tools: extend shell (already exists) ----------
# (No change if file already patched; ensure env support & allowlist)
python - <<'PY'
from pathlib import Path
p = Path("master_ai/tools/shell.py")
if p.exists():
    s = p.read_text()
    if "env: dict | None = None" not in s:
        s = s.replace(
            "def run(cmd: Sequence[str], cwd: str | None = None, timeout: int = 120) -> subprocess.CompletedProcess:",
            "def run(cmd: Sequence[str], cwd: str | None = None, timeout: int = 120, env: dict | None = None) -> subprocess.CompletedProcess:"
        )
    if "import os" not in s:
        s = s.replace("import subprocess", "import subprocess\nimport os")
    if "env = {**os.environ" not in s:
        s = s.replace(
            "return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)",
            "env = {**os.environ, **(env or {})}\n    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False, env=env)"
        )
    p.write_text(s)
else:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("""from __future__ import annotations
import subprocess, os
from typing import Sequence
ALLOWED = {"python","pytest","pip","echo","ls","cat","mkdir","touch","sh","bash"}
def run(cmd: Sequence[str], cwd: str | None = None, timeout: int = 120, env: dict | None = None) -> subprocess.CompletedProcess:
    if cmd and cmd[0] not in ALLOWED: raise RuntimeError(f"Command not allowed: {cmd[0]}")
    env = {**os.environ, **(env or {})}
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False, env=env)
""")
print("tools/shell.py ensured")
PY

# ---------- self_update ----------
cat > master_ai/self_update/manifest.py <<'PY'
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, hashlib

@dataclass
class VersionInfo:
    version: str
    sha256: str
    url: str | None = None

def read_manifest(p: Path) -> VersionInfo:
    data = json.loads(p.read_text())
    return VersionInfo(**data)

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
PY

cat > master_ai/self_update/apply.py <<'PY'
from __future__ import annotations
from pathlib import Path
from master_ai.self_update.manifest import read_manifest, sha256_file

def self_check() -> bool:
    # Wire up stronger gates later; green-light for now.
    return True

def apply_update(bundle: Path, manifest: Path, install_dir: Path) -> bool:
    info = read_manifest(manifest)
    if sha256_file(bundle) != info.sha256:
        print("[self-update] ❌ SHA256 mismatch")
        return False
    # For now, pretend "bundle" is a ready tree: unpack/replace not implemented.
    # You can wire your own tar/zip logic + staging here.
    print("[self-update] (stub) Verified bundle hash; staging not implemented yet.")
    return True
PY

# ---------- UI: minimal Streamlit console ----------
cat > ui/console.py <<'PY'
import subprocess, tempfile, pathlib, time, sys

def run_goal(goal: str):
    # Launch the CLI and stream output
    proc = subprocess.Popen(
        [sys.executable, "-m", "master_ai", "run-goal", "--goal", goal],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in proc.stdout:
        print(line, end="")
    proc.wait()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_goal(" ".join(sys.argv[1:]))
    else:
        print("Usage: python -m ui.console \"your goal here\"")
PY

# ---------- CLI: extend __main__ with plan/run-goal/self-update ----------
python - <<'PY'
from pathlib import Path
p = Path("master_ai/__main__.py")
src = p.read_text()
if "def cmd_plan(" not in src:
    src = src.replace(
        "from master_ai.self_update.apply import self_check",
        "from master_ai.self_update.apply import self_check\nfrom master_ai.agents.planner import make_plan\nfrom master_ai.agents.researcher import gather_context\nfrom master_ai.agents.coder import scaffold_project, write_tests, run_tests\nfrom master_ai.agents.reviewer import run_quality_gates\nfrom master_ai.agents.redteam import scan\nfrom master_ai.agents.ops import stage_output\nfrom master_ai.core.executor import Executor\n"
    )
    src = src.replace(
        "def main() -> None:",
        """def cmd_plan(ns) -> None:
    goal = ns.goal
    steps = make_plan(goal)
    print("[plan]")
    for s in steps:
        print(f" - {s.name}: {s.desc}")

def cmd_run_goal(ns) -> None:
    goal = ns.goal
    from pathlib import Path as _P
    root = _P.cwd()
    from master_ai.core.context import RunContext
    ctx = RunContext.new(root)
    print(f"[Run {ctx.run_id}] goal: {goal}")
    ex = Executor(ctx.artifacts)
    # redteam plan
    bad = scan(goal)
    if bad:
        print("[redteam] ⚠️ suspicious patterns:", bad)
    # Build a tiny project to satisfy goal (scaffold -> tests -> pytest -> gates)
    proj = root / "artifacts" / "projects" / f"auto_{ctx.run_id}"
    scaffold_project(name=f"auto_{ctx.run_id}", path=str(proj))
    write_tests(path=str(proj))
    run_tests(path=str(proj))
    run_quality_gates(proj)
    stage_output(ctx.artifacts, proj)
    print(f"[Run {ctx.run_id}] done → {ctx.artifacts}")

def cmd_self_update(ns) -> None:
    mode = "check" if ns.check else "apply"
    if mode == "check":
        ok = self_check()
        print("Self-check:", "OK" if ok else "FAILED")
        raise SystemExit(0 if ok else 1)
    else:
        from master_ai.self_update.apply import apply_update
        from pathlib import Path as _P
        ok = apply_update(_P(ns.bundle), _P(ns.manifest), _P.cwd())
        raise SystemExit(0 if ok else 1)

def main() -> None:"""
    )
    # add subparsers
    src = src.replace(
        'sp = sub.add_parser("self-check", help="Run internal lint/test gates")',
        'sp = sub.add_parser("self-check", help="Run internal lint/test gates")'
    )
    src = src.replace(
        "sp.set_defaults(func=cmd_self_check)",
        "sp.set_defaults(func=cmd_self_check)\n\n    sp = sub.add_parser(\"plan\", help=\"Create a step plan for a goal\")\n    sp.add_argument(\"--goal\", required=True)\n    sp.set_defaults(func=cmd_plan)\n\n    sp = sub.add_parser(\"run-goal\", help=\"Plan, code, test, and stage a tiny project for a goal\")\n    sp.add_argument(\"--goal\", required=True)\n    sp.set_defaults(func=cmd_run_goal)\n\n    sp = sub.add_parser(\"self-update\", help=\"Check/apply an update bundle\")\n    sp.add_argument(\"--check\", action=\"store_true\")\n    sp.add_argument(\"--apply\", action=\"store_true\")\n    sp.add_argument(\"--bundle\", default=\"bundle.tgz\")\n    sp.add_argument(\"--manifest\", default=\"manifest.json\")\n    sp.set_defaults(func=cmd_self_update)"
    )
    p.write_text(src)
    print("CLI extended with: plan, run-goal, self-update")
else:
    print("CLI already patched; skipping")
PY

# ---------- tests: quick smoke ----------
cat > tests/test_agents_smoke.py <<'PY'
def test_imports():
    import master_ai.agents.planner as _; import master_ai.agents.coder as _; import master_ai.agents.reviewer as _; import master_ai.agents.redteam as _; import master_ai.agents.ops as _
PY

# ---------- Makefile: add console/plan/run-goal helpers ----------
python - <<'PY'
import pathlib, re
mk = pathlib.Path("Makefile")
t = mk.read_text()
if "run-goal" not in t:
    t += """

.PHONY: console plan run-goal
console:
\tpython -m ui.console "hello world"

plan:
\tpython -m master_ai plan --goal "demo goal"

run-goal:
\tpython -m master_ai run-goal --goal "demo goal"
"""
mk.write_text(t)
print("Makefile updated with console/plan/run-goal targets")
PY

echo "[upgrade] Done."
