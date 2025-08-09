import smtplib

GMAIL_ADDRESS = "visserlotte87@gmail.com"
CREDS_FILE = "creds.txt"

with open(CREDS_FILE) as f:
    passwords = [line.strip() for line in f if line.strip()]

# Include the password you gave explicitly, in case it's not in the file
passwords = ["zwjwismiqrqeuaxz"] + [p for p in passwords if p != "zwjwismiqrqeuaxz"]

success = False
for pwd in passwords:
    try:
        print(f"🔐 Trying: {pwd}")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_ADDRESS, pwd)
            print(f"✅ SUCCESS: {pwd}")
            success = True
            break
    except smtplib.SMTPAuthenticationError as e:
        print("❌ Failed:", e.smtp_error.decode())
    except Exception as e:
        print("❌ Error:", str(e))

if not success:
    print("🚫 No valid passwords found.")
