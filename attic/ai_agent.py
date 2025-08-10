"""
ai_agent.py
Autonomous agent that:
1. polls Gmail every minute
2. processes commands from alexbraithwaite02@icloud.com
3. emails crash reports back to alexbraithwaite02@icloud.com
4. auto-heals & restarts on patch approval
"""

import base64
import logging
import os
import pathlib
import sys
import time
import traceback

from googleapiclient.errors import HttpError

from gmail_service import gmail_service

OWNER = "alexbraithwaite02@icloud.com"  # receive crash / patch emails
FROM_ADDRESS = "visserlotte87@gmail.com"  # sending account
POLL_SEC = 60

LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "automation.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


# ------------------------------------------------------------------- helpers
def send_mail(service, to, subject, body):
    import base64
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["to"] = to
    msg["from"] = FROM_ADDRESS
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _decode_message(msg):
    """Return plain-text body (best-effort)."""
    parts = msg["payload"].get("parts", [])
    data = None
    if parts:
        data = parts[0]["body"].get("data")
    else:
        data = msg["payload"]["body"].get("data")
    if not data:
        return ""
    return base64.urlsafe_b64decode(data).decode(errors="ignore")


def _apply_patch(patch_text):
    """Write patch_text into ai_agent.py (very naive replacement)."""
    with open(__file__, "w", encoding="utf-8") as f:
        f.write(patch_text)
    logging.info("Applied self-patch; restarting")
    os.execl(sys.executable, sys.executable, __file__)  # replace process


# ------------------------------------------------------------------- core loop
def poll_loop():
    service = gmail_service()
    logging.info("AI-Agent started; polling every %s s", POLL_SEC)

    while True:
        try:
            # ── read *unread* messages sent to FROM_ADDRESS
            resp = (
                service.users()
                .messages()
                .list(userId="me", q="is:unread", maxResults=10)
                .execute()
            )
            for m in resp.get("messages", []):
                full = service.users().messages().get(userId="me", id=m["id"]).execute()
                body = _decode_message(full).strip()

                # mark read ASAP
                service.users().messages().modify(
                    userId="me",
                    id=m["id"],
                    body={"removeLabelIds": ["UNREAD"]},
                ).execute()

                # simple command router
                body_lc = body.lower()
                if body_lc.startswith("stop"):
                    logging.info("Stop command received – shutting down")
                    send_mail(
                        service,
                        OWNER,
                        "AI-Agent stopped",
                        "Agent stopped gracefully on command.",
                    )
                    sys.exit(0)

                if body_lc.startswith("patch:"):
                    patch = body.partition(":")[2].lstrip()
                    _apply_patch(patch)

                # … extend with more commands as needed …

            time.sleep(POLL_SEC)

        except (HttpError, Exception):
            tb = traceback.format_exc()
            logging.error("Crash: %s", tb)
            # notify owner
            try:
                send_mail(
                    gmail_service(),  # fresh service in case creds were invalid
                    OWNER,
                    "AI-Agent crash report",
                    tb,
                )
            except Exception as mail_exc:
                logging.error("Could not send crash email: %s", mail_exc)
            # short back-off then restart loop
            time.sleep(30)
            service = gmail_service()


# ------------------------------------------------------------------- main
if __name__ == "__main__":
    try:
        poll_loop()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt – exiting.")
