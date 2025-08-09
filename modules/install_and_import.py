# install_and_import.py
"""
Master-AI Self-Healing Module Installer
Automatically installs and imports any Python package needed during runtime.
"""

import importlib
import subprocess
import sys


def install_and_import(package_name: str, alias: str = None):
    try:
        # Attempt to import the module
        return importlib.import_module(alias or package_name)
    except ImportError:
        print(f"📦 Installing missing package: {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return importlib.import_module(alias or package_name)


# === Example Usage ===
if __name__ == "__main__":
    # Example: install and import requests
    requests = install_and_import("requests")
    print("✅ requests installed and imported successfully")
