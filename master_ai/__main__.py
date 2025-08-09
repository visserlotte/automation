# master_ai/__main__.py
from __future__ import annotations

import argparse
from pathlib import Path as _P

from master_ai.agents.coder import run_tests, scaffold_project, write_tests
from master_ai.agents.ops import stage_output
from master_ai.agents.planner import make_plan
from master_ai.agents.redteam import scan
from master_ai.agents.reviewer import run_quality_gates
from master_ai.core.context import RunContext
from master_ai.self_update.apply import self_check


def cmd_self_check(_: argparse.Namespace) -> None:
    ok = self_check()
    print("Self-check:", "OK" if ok else "FAILED")
    raise SystemExit(0 if ok else 1)


def cmd_plan(ns: argparse.Namespace) -> None:
    goal = ns.goal
    steps = make_plan(goal)
    print("[plan]")
    for s in steps:
        print(f" - {s.name}: {s.desc}")


def cmd_run_goal(ns: argparse.Namespace) -> None:
    goal = ns.goal
    root = _P.cwd()
    ctx = RunContext.new(root)
    print(f"[Run {ctx.run_id}] goal: {goal}")

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


def cmd_agent_run(ns):
    from master_ai.runtime.agent import Agent
    from pathlib import Path
    runs = Path('artifacts/runs')
    agent = Agent(goal=ns.goal, root=runs, safe_mode=(not ns.unsafe))
    rc = agent.run()
    raise SystemExit(rc)


def cmd_self_update(ns: argparse.Namespace) -> None:
    mode = "check" if ns.check else "apply"
    if mode == "check":
        ok = self_check()
        print("Self-check:", "OK" if ok else "FAILED")
        raise SystemExit(0 if ok else 1)
    else:
        from master_ai.self_update.apply import apply_update
        ok = apply_update(_P(ns.bundle), _P(ns.manifest), _P.cwd())
        raise SystemExit(0 if ok else 1)


def main() -> None:
    p = argparse.ArgumentParser("master_ai", description="Master-AI vNext CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("agent-run", help="Run the agent against a goal")
    sp.add_argument("--goal", required=True)
    sp.add_argument("--unsafe", action="store_true",
                    help="Disable allowlist and use shell=True")
    sp.set_defaults(func=cmd_agent_run)

    sp = sub.add_parser("self-check", help="Run internal lint/test gates")
    sp.set_defaults(func=cmd_self_check)

    sp = sub.add_parser("plan", help="Create a step plan for a goal")
    sp.add_argument("--goal", required=True)
    sp.set_defaults(func=cmd_plan)

    sp = sub.add_parser("run-goal",
                        help="Plan, code, test, and stage a tiny project for a goal")
    sp.add_argument("--goal", required=True)
    sp.set_defaults(func=cmd_run_goal)

    sp = sub.add_parser("self-update", help="Check/apply an update bundle")
    sp.add_argument("--check", action="store_true")
    sp.add_argument("--apply", action="store_true")
    sp.add_argument("--bundle", default="bundle.tgz")
    sp.add_argument("--manifest", default="manifest.json")
    sp.set_defaults(func=cmd_self_update)

    ns = p.parse_args()
    ns.func(ns)


if __name__ == "__main__":
    main()
