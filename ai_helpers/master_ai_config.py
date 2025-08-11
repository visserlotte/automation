import os
import pathlib

import openai
from dotenv import load_dotenv

ENV_PATH = pathlib.Path.home() / "automation" / ".env"
load_dotenv(ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GMAIL = os.getenv("GMAIL_ADDRESS")
GPASS = os.getenv("GMAIL_PASSWORD")
REPLY = os.getenv("REPLY_TO")
PROJECT = os.getenv("PROJECT", "default")
PORT = int(os.getenv("PORT", "55555"))

missing = [
    k
    for k, v in {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "GMAIL": GMAIL,
        "GPASS": GPASS,
        "REPLY": REPLY,
    }.items()
    if not v
]
if missing:
    print(f"[config] ⚠️ missing env vars: {', '.join(missing)} – continuing in offline mode")

openai.api_key = OPENAI_API_KEY
