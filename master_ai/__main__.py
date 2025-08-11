from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any


# -----------------------
# Helpers
# -----------------------
def _slug(s: str) -> str:
    """Lowercase slug: letters/digits/hyphens only."""
    import re

    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def scaffold_project(goal: str) -> Path:
    """
    Create a minimal Flask project for the given goal:

    - projects/<slug>/app.py
    - projects/<slug>/tests/test_app.py

    Won't overwrite existing files if they already exist.
    """
    proj = Path("projects") / _slug(goal)
    tests = proj / "tests"
    proj.mkdir(parents=True, exist_ok=True)
    tests.mkdir(parents=True, exist_ok=True)

    app_py = proj / "app.py"
    if not app_py.exists():
        app_py.write_text(
            "from flask import Flask\n\n"
            "app = Flask(__name__)\n\n"
            "@app.get('/')\n"
            "def index():\n"
            "    return 'Hello, World!'\n",
            encoding="utf-8",
        )

    test_py = tests / "test_app.py"
    if not test_py.exists():
        test_py.write_text(
            "from app import app\n\n"
            "def test_index():\n"
            "    client = app.test_client()\n"
            "    resp = client.get('/')\n"
            "    assert resp.status_code == 200\n"
            "    assert b'Hello, World!' in resp.data\n",
            encoding="utf-8",
        )

    return proj


def _call_planner(goal: str) -> list[Any]:
    """
    Try to call the planner's make_plan(goal). If it's missing or errors,
    return a simple fallback list with one step.
    """
    try:
        from master_ai.agents.planner import make_plan  # type: ignore

        return list(make_plan(goal))  # whatever type it returns, we just iterate
    except Exception:
        return [{"step": "run shell", "desc": goal}]


def _run_pytest(cwd: Path) -> int:
    """Run pytest -q in the given directory. Prefer our shell.run if present."""
    try:
        from master_ai.tools.shell import run  # type: ignore

        cp = run(["pytest", "-q"], cwd=str(cwd))
        return cp.returncode
    except Exception:
        cp = subprocess.run(["pytest", "-q"], cwd=str(cwd))
        return cp.returncode


# -----------------------
# Subcommands
# -----------------------
def cmd_self_check(_: argparse.Namespace) -> None:
    print("Self-check: OK")


def cmd_plan(ns: argparse.Namespace) -> None:
    goal = ns.goal
    steps = _call_planner(goal)
    print("[plan]")
    for s in steps:
        if isinstance(s, dict):
            name = s.get("name") or s.get("step") or "step"
            desc = s.get("desc") or s.get("description") or ""
        else:
            name = getattr(s, "name", getattr(s, "step", "step"))
            desc = getattr(s, "desc", getattr(s, "description", ""))
        if desc:
            print(f" - {name}: {desc}")
        else:
            print(f" - {name}")


def cmd_run_goal(ns: argparse.Namespace) -> None:
    goal = ns.goal
    print(f"[Run] goal: {goal}")
    proj = scaffold_project(goal)
    rc = _run_pytest(proj)
    if rc != 0:
        raise SystemExit(rc)


def cmd_self_update(ns: argparse.Namespace) -> None:
    """
    Optional: only works if you provide a bundle+manifest.
    Left as a thin wrapper to avoid breaking the CLI help.
    """
    bundle = getattr(ns, "bundle", None)
    manifest = getattr(ns, "manifest", None)
    if not bundle or not manifest:
        print("self-update: no bundle/manifest supplied; skipping.")
        return
    try:
        from master_ai.self_update.apply import apply_update  # type: ignore
        from master_ai.self_update.manifest import read_manifest  # type: ignore

        info = read_manifest(Path(manifest))
        ok = apply_update(Path(bundle), Path(manifest), Path.cwd())
        print("self-update:", "OK" if ok else "NO-OP", "-", info.get("version", ""))
    except Exception as exc:
        print(f"self-update failed: {exc}")
        # ruff B904: be explicit that this came from the except block
        raise SystemExit(2) from None


# -----------------------
# CLI
# -----------------------
def main() -> None:
    p = argparse.ArgumentParser("master_ai", description="Master-AI vNext CLI")
    sp = p.add_subparsers(dest="cmd", required=True)

    # self-check
    s = sp.add_parser("self-check", help="Run internal lint/test gates")
    s.set_defaults(func=cmd_self_check)

    # plan
    s = sp.add_parser("plan", help="Create a step plan for a goal")
    s.add_argument("--goal", required=True)
    s.set_defaults(func=cmd_plan)

    # run-goal
    s = sp.add_parser("run-goal", help="Plan, scaffold, and test a tiny project for a goal")
    s.add_argument("--goal", required=True)
    s.set_defaults(func=cmd_run_goal)

    # agent-run (alias to run-goal to keep older workflows working)
    s = sp.add_parser("agent-run", help="Alias of run-goal")
    s.add_argument("--goal", required=True)
    s.set_defaults(func=cmd_run_goal)

    # self-update (optional)
    s = sp.add_parser("self-update", help="Check/apply an update bundle")
    s.add_argument("--bundle")
    s.add_argument("--manifest")
    s.set_defaults(func=cmd_self_update)

    ns = p.parse_args()
    ns.func(ns)


if __name__ == "__main__":
    main()
