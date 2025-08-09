from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file(
    "credentials.json", ["https://www.googleapis.com/auth/gmail.readonly"]
)

service = build("gmail", "v1", credentials=creds)
results = service.users().messages().list(userId="me", maxResults=5).execute()
messages = results.get("messages", [])

print("Recent email IDs:")
for msg in messages:
    print(msg["id"])
