import os
from datetime import datetime

log_path = os.path.expanduser("~/automation/logs/ai_brain.log")
thoughts_path = os.path.expanduser("~/automation/logs/thoughts.log")
tools_path = os.path.expanduser("~/automation/tools/")

os.makedirs(tools_path, exist_ok=True)


def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as log_file:
        log_file.write(f"[{now}] {msg}\n")


def think(thought):
    with open(thoughts_path, "a") as t:
        t.write(f"[THOUGHT] {thought}\n")


def build_feature(name, content):
    feature_path = os.path.join(tools_path, name)
    with open(feature_path, "w") as f:
        f.write(content)
    os.chmod(feature_path, 0o755)
    log(f"✅ Created tool: {name}")


if __name__ == "__main__":
    log("🧠 Brain bootstrap launched...")
    think("Let’s start with basic system upgrades and tools.")

    # Example tool: system scan
    tool_code = """#!/bin/bash
echo "🔒 Running security scan..."
uptime
df -h
"""
    build_feature("security_scan.sh", tool_code)

    think("Next, let’s monitor logs and detect idle patterns.")
    log("🧠 Brain upgrade phase complete.")
