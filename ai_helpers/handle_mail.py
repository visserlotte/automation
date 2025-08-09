#!/usr/bin/env python3
import datetime as dt
import email
import pathlib
import re
import subprocess
import sys

raw = sys.stdin.read()
msg = email.message_from_string(raw)
body = msg.get_payload(decode=True).decode(errors="ignore")

# archive every inbound message
archive = pathlib.Path("/home/ubuntu/automation/mail_in")
archive.mkdir(exist_ok=True, parents=True)
with open(archive / f"{dt.datetime.utcnow().isoformat()}.eml", "w") as f:
    f.write(raw)

# very simple commands
if re.search(r"\bwake\b", body, re.I):
    subprocess.run(["systemctl", "start", "ai-wake.timer"])
elif re.search(r"\bsleep\b", body, re.I):
    subprocess.run(["systemctl", "start", "ai-suspend.service"])
else:
    # hand the body to your normal AI runner
    subprocess.run(["/home/ubuntu/automation/start_ai.sh"], input=body.encode())
