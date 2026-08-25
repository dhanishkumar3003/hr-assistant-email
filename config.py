"""
Configuration management for email automation.

Loads and validates environment variables required for Gmail
SMTP/IMAP communication.
"""

import os
import sys
import logging
from dotenv import load_dotenv

log = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Gmail credentials
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# File paths
STATE_FILE = "candidates_state.json"

# Monitoring settings
POLL_INTERVAL_SECONDS = 15
MAX_MONITOR_MINUTES = 60

# Gmail server settings
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_SMTP_PORT = 587


def require_config():
    """
    Validate that all required configuration is present.
    
    Raises:
        SystemExit: If any required environment variable is missing.
    """
    missing = [
        key
        for key, value in {
            "GMAIL_ADDRESS": GMAIL_ADDRESS,
            "GMAIL_APP_PASSWORD": GMAIL_APP_PASSWORD,
        }.items()
        if not value
    ]

    if missing:
        log.error(
            f"Missing required .env values: {', '.join(missing)}"
        )
        sys.exit(2)
