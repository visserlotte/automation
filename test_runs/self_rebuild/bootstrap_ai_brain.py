import os
from datetime import datetime

log_path = os.path.expanduser("~/automation/logs/ai_updates.log")
master_path = os.path.expanduser("~/automation/master_ai.py")


def log(msg):
    with open(log_path, "a") as log_file:
        log_file.write(f"[{datetime.now()}] {msg}\n")


def safe_patch_brain():
    try:
        with open(master_path) as f:
            contents = f.read()
            if "SELF_EXPANDING_FEATURES" in contents:
                log("🧠 Already patched with self-expanding features.")
                return

        new_logic = """

# === SELF_EXPANDING_FEATURES ===
def build_new_feature(feature_name, code_block):
    try:
        with open(__file__, 'a') as f:
            f.write(f"\\n# Feature: {feature_name}\\n")
            f.write(code_block + "\\n")
        return f"✅ Feature '{feature_name}' added successfully."
    except Exception as e:
        return f"❌ Failed to add feature '{feature_name}': {e}"
"""

        with open(master_path, "a") as f:
            f.write(new_logic)

        log("✅ Self-expanding logic added to master_ai.py.")

    except Exception as e:
        log(f"❌ Error patching brain: {e}")


if __name__ == "__main__":
    log("🔧 Running brain patcher...")
    safe_patch_brain()
