import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/automation/edit_log.txt")


def write_code(filename, code):
    with open(filename, "w") as f:
        f.write(code)
    log_edit(filename)


def append_code(filename, code):
    with open(filename, "a") as f:
        f.write("\n" + code)
    log_edit(filename)


def log_edit(filename):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] Edited {filename}\n")
