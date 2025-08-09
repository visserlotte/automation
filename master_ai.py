#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from master_ai.agents.planner import plan_build_project
from master_ai.core.context import RunContext
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


def dummy(*_a, **_k):
    """Auto-added shim by fixers.py (until real implementation exists)."""
    pass


def not_exist_mod(*_a, **_k):
    """Auto-added shim by fixers.py (until real implementation exists)."""
    pass
