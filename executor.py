import pathlib
import subprocess
import sys
import textwrap

from ai_helpers.ai_utils import gpt

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent


def apply_plan(steps: list[str]) -> None:
    """
    Very first-pass self-builder:

    • Looks for lines that mention a *.py file
    • Asks GPT for the full file content (or improved version)
    • Writes/overwrites the file, then runs pytest
    """
    for step in steps:
        # Find the first token that ends in .py
        target = next((tok for tok in step.split() if tok.endswith(".py")), None)
        if not target:
            continue

        path = PROJECT_ROOT / target
        context = path.read_text() if path.exists() else "[NEW FILE]"

        prompt = textwrap.dedent(f"""
            You are an autonomous coding agent. Generate the *complete* content
            for {target}. If the file already exists, overwrite it with an
            improved version that fulfils the current goal.

            === CURRENT CONTENT ===
            {context}
        """)

        code = gpt(prompt)
        path.write_text(code)
        print(f"[executor] wrote {target}")

    _run_tests()


def _run_tests() -> None:
    """Run pytest and show a one-line summary."""
    print("[executor] running pytest …")
    subprocess.call([sys.executable, "-m", "pytest", "-q"])
