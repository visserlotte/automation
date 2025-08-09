# scripts/generate_gmail_creds.py

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

auth_url, _ = flow.authorization_url(prompt="consent")

print("Go to the following URL and authorize the app:\n")
print(auth_url)

code = input("\nPaste the authorization code here: ")

flow.fetch_token(code=code)

creds = flow.credentials
with open("token.json", "w") as token:
    token.write(creds.to_json())

print("\n✅ Token successfully saved to token.json.")
