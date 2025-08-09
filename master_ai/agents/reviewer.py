from __future__ import annotations

from pathlib import Path

from master_ai.tools.shell import run


def run_quality_gates(project_path: Path) -> None:
    # format + typecheck
    run(["ruff", "format", "."], cwd=str(project_path))
    run(["mypy", "."], cwd=str(project_path))
    # tests
    cp = run(["pytest", "-q"], cwd=str(project_path))
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)
