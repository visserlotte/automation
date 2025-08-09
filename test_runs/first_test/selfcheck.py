import os
from datetime import datetime

import requests

log_file_path = os.path.expanduser("~/automation/test_runs/first_test/status_log.txt")


def log_status():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        public_ip = requests.get("https://api.ipify.org").text
        with open(log_file_path, "w") as f:
            f.write(f"Time: {now}\n")
            f.write(f"Public IP: {public_ip}\n")
        return True
    except Exception as e:
        with open(log_file_path, "a") as f:
            f.write(f"Error: {str(e)}\n")
        return False


if __name__ == "__main__":
    log_status()
