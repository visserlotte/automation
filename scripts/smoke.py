import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(".env")

# OpenAI ping
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resp = client.chat.completions.create(
    model="gpt-4o-mini", messages=[{"role": "user", "content": "Say hi in 3 words."}]
)
print("OpenAI OK:", resp.choices[0].message.content)

# Email ping (optional; only runs if SMTP creds exist)
smtp_user = os.getenv("SMTP_USERNAME")
smtp_pass = os.getenv("SMTP_PASSWORD")
notify = os.getenv("NOTIFY_EMAIL")
server = os.getenv("SMTP_SERVER")
port = int(os.getenv("SMTP_PORT") or 0)

if all([smtp_user, smtp_pass, notify, server, port]):
    msg = EmailMessage()
    msg["Subject"] = "Automation smoke test"
    msg["From"] = smtp_user
    msg["To"] = notify
    msg.set_content("It works! ✅")
    with smtplib.SMTP(server, port) as s:
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)
    print("Email OK: sent to", notify)
else:
    print("Email skipped (missing SMTP_* or NOTIFY_EMAIL in .env)")
