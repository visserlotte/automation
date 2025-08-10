import subprocess
import sys


def run_goal(goal: str):
    # Launch the CLI and stream output
    proc = subprocess.Popen(
        [sys.executable, "-m", "master_ai", "run-goal", "--goal", goal],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in proc.stdout:
        print(line, end="")
    proc.wait()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_goal(" ".join(sys.argv[1:]))
    else:
        print('Usage: python -m ui.console "your goal here"')
