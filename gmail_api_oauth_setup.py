import os
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no valid credentials, let user log in.
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        auth_url, _ = flow.authorization_url(prompt="consent")
        print("Go to this URL and authorize:\n", auth_url)
        code = input("Paste the authorization code here: ")
        creds = flow.fetch_token(code=code)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=5).execute()
    messages = results.get("messages", [])
    print("Recent email IDs:")
    for msg in messages:
        print(msg["id"])


if __name__ == "__main__":
    main()
