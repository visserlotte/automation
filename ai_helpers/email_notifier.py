import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

# Load .env from project root automatically (first call is a no-op if already loaded)
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")


def send(subject: str, body: str) -> None:
    """Send a plain-text email or raise RuntimeError if creds are missing."""
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD, NOTIFY_EMAIL]):
        raise RuntimeError("Email creds not set")

    msg = MIMEMultipart()
    msg["From"], msg["To"], msg["Subject"] = SMTP_USER, NOTIFY_EMAIL, subject
    msg.attach(MIMEText(body, "plain"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as srv:
        srv.starttls(context=ctx)
        srv.login(SMTP_USER, SMTP_PASSWORD)
        srv.send_message(msg)
