import json
import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    creds = None
    creds_path = "credentials.json"
    token_path = "creds/token.pickle"

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            with open(creds_path) as f:
                client_config = json.load(f)

            flow = Flow.from_client_config(
                client_config, scopes=SCOPES, redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )

            auth_url, _ = flow.authorization_url(prompt="consent")
            print("🔗 Visit this URL to authorize:\n", auth_url)

            code = input("📥 Enter the authorization code: ")
            flow.fetch_token(code=code)
            creds = flow.credentials

        os.makedirs("creds", exist_ok=True)
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    print("✅ Gmail authentication successful.")


if __name__ == "__main__":
    main()
