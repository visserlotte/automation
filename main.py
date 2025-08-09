import logging
import os

import yaml

# Load config
with open("config/config.yaml") as file:
    config = yaml.safe_load(file)

# Basic logger
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/automation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Startup banner
print("🚀 Automation system booted successfully")
logging.info("System started")

# Example: print AWS bucket name
print(f"Using bucket: {config['aws']['bucket_name']}")
