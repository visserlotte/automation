import base64
import logging
import os
import time
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ------------------ CONFIGURATION ------------------ #
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_PATH = "token.pickle"
CREDS_PATH = "credentials.json"
ALERT_TO_EMAIL = "alexbraithwaite02@icloud.com"
ALERT_FROM_EMAIL = "visserlotte87@gmail.com"
KEYWORDS = ["error", "crash", "failed", "traceback"]
POLL_INTERVAL = 60  # seconds

# ------------------ LOGGING SETUP ------------------ #
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)


# ------------------ AUTHENTICATION ------------------ #
def gmail_authenticate():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


# ------------------ EMAIL UTILITIES ------------------ #
def create_message(sender, to, subject, body):
    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_email(service, to, subject, body):
    message = create_message(ALERT_FROM_EMAIL, to, subject, body)
    service.users().messages().send(userId="me", body=message).execute()


# ------------------ MAIN MONITOR LOOP ------------------ #
def check_emails(service):
    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], q="is:unread")
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        logging.info("No new emails.")
        return

    for msg in messages:
        msg_id = msg["id"]
        full_msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        snippet = full_msg.get("snippet", "").lower()

        if any(keyword in snippet for keyword in KEYWORDS):
            subject = "⚠️ AI System Crash Detected"
            body = f"Crash detected in email snippet:\n\n{snippet}"
            send_email(service, ALERT_TO_EMAIL, subject, body)
            logging.warning(f"Crash email forwarded to {ALERT_TO_EMAIL}")
        else:
            logging.info("No crash keywords found in unread email.")

        # Mark as read
        service.users().messages().modify(
            userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()


# ------------------ START AGENT ------------------ #
def main():
    logging.info("✅ AI-Agent running. Polling Gmail every 60s...")
    service = gmail_authenticate()

    while True:
        try:
            check_emails(service)
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            logging.error(f"AI-Agent error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
