from __future__ import annotations

from pathlib import Path

from master_ai.tools.shell import run

TEMPLATE_MAIN = """def run():
    return "hello"

if __name__ == "__main__":
    print(run())
"""

TEMPLATE_README = "# {name}\n\nSimple auto-generated CLI.\n\n```\npython -m {name}\n```"

TEMPLATE_INIT = "__all__ = []\n"

TEMPLATE_TEST = """from {name} import app

def test_run():
    assert app.run() == "hello"
"""


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
    (root / "tests" / "conftest.py").write_text("""\
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
""")
    # refer to module as package import
    pkg = next(d.name for d in root.iterdir() if d.is_dir() and d.name != "tests")
    (root / "tests" / "test_app.py").write_text(TEMPLATE_TEST.format(name=pkg))


def run_tests(path: str) -> None:
    cp = run(["pytest", "-q"], cwd=path)
    print(cp.stdout.strip())
    if cp.returncode != 0:
        print(cp.stderr)
        raise SystemExit(cp.returncode)
