import pickle

from googleapiclient.discovery import build

# Load your credentials from the token.pickle file
with open("/home/ubuntu/automation/token.pickle", "rb") as token:
    creds = pickle.load(token)

# Connect to Gmail API and print all labels in your account
service = build("gmail", "v1", credentials=creds)
results = service.users().labels().list(userId="me").execute()
labels = results.get("labels", [])
print("Labels:")
for label in labels:
    print(label["name"])
