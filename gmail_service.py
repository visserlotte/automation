# ---------- gmail_service.py  ----------
import logging
import pathlib
import pickle
import smtplib

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDS_DIR = pathlib.Path("~/automation/creds").expanduser()
CREDS_DIR.mkdir(exist_ok=True, parents=True)
TOKEN_FILE = CREDS_DIR / "token.pickle"
CLIENT_FILE = CREDS_DIR / "credentials.json"


def gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = pickle.loads(TOKEN_FILE.read_bytes())

    # ── 1. silently refresh if possible ───────────────────────────
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_bytes(pickle.dumps(creds))
            logging.info("✅ token refreshed silently")
        except Exception as e:
            logging.warning(f"⚠️ token refresh failed: {e}")

    # ── 2. if still no valid creds, fall back to browser flow ─────
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, SCOPES)
        flow.run_local_server(port=0)  # <-- one-time browser step
        creds = flow.credentials
        TOKEN_FILE.write_bytes(pickle.dumps(creds))
        _notify_reauth("New OAuth token stored.")

    from googleapiclient.discovery import build

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# ------------ helper -------------------------------------------
def _notify_reauth(msg):
    """Send yourself an alert so you know re-auth happened."""
    FROM = "visserlotte87@gmail.com"
    TO = "alexbraithwaite02@icloud.com"
    body = f"Subject: [AI-Agent] Gmail re-authorised\n\n{msg}"
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(FROM, "❗app-password-or-OAuth2❗")  #  ➜ or use Gmail SMTP OAuth2
        s.sendmail(FROM, TO, body.encode())


# ---------------------------------------------------------------
