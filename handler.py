"""
Minimal Lambda entrypoint for Master-AI container.
If imports fail, return JSON diagnostics instead of crashing.
"""

import os
import sys
import traceback


def lambda_handler(event, context):
    try:
        from master_ai import gpt_chat

        task = (event or {}).get("task", "ping")
        return gpt_chat(task)
    except Exception as e:
        return {
            "status": "import_error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "ls_var_task": os.listdir("/var/task") if os.path.isdir("/var/task") else [],
        }
