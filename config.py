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

# Gmail account identity. Authentication is handled by gmail_auth.py.
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Monitoring settings
POLL_INTERVAL_SECONDS = 15
MAX_MONITOR_MINUTES = 60

# Gmail server settings
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_SMTP_PORT = 587

# Ollama LLM settings (reply classification fallback)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Reply classification rules (reply_classifier.py)
#
# Auto-replies aren't a real response from the candidate - route straight
# to review instead of risking a false interested/declined match on
# whatever boilerplate the OOO message happens to contain.
REPLY_AUTO_REPLY_PATTERNS = [
    r"\bout of office\b",
    r"\bautomatic reply\b",
    r"\bauto-reply\b",
    r"\bi\s*am\s*currently\s*out\b",
    r"\bon\s*(vacation|leave|pto)\b",
    r"\bcurrently unavailable\b",
]

# Checked before interest patterns so mixed replies ("interested, but I
# have to pass") land on decline rather than a false positive.
REPLY_DECLINED_PATTERNS = [
    r"\bnot interested\b",
    r"\bno longer interested\b",
    r"\bnot a good fit\b",
    r"\bpursuing other opportunities\b",
    r"\baccepted (another|a different) (offer|position|role)\b",
    r"\bwithdraw(ing)?\s*my\s*application\b",
    r"\bplease remove me\b",
    r"\bunsubscribe\b",
    r"\bno thanks?\b",
    r"\bnot\s*(moving forward|the right time|right now)\b",
    r"\bi(?:'|’)?ll(?:\s+\w+){0,3}\s+pass\b",
    r"\bdecline\b",
    r"\bnot\s*a\s*match\b",
]

REPLY_INTERESTED_PATTERNS = [
    r"\byes\b",
    r"\bi(?:'|’)?m\s*interested\b",
    r"\bi\s*am\s*interested\b",
    r"\bsounds good\b",
    r"\bcount me in\b",
    r"\b(i(?:'|’)?d|i would) love to\b",
    r"\bhappy to\b",
    r"\blet(?:'|’)?s schedule\b",
    r"\b(i(?:'|’)?m|i am)\s*available\b",
    r"\bworks for me\b",
    r"\blooking forward\b",
    r"\bplease send\b",
    r"\bi confirm\b",
    r"\bi accept\b",
    r"\bwhen can we\b",
    r"\bwhat time works\b",
    r"\binterested\b",
]


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
            "DATABASE_URL": DATABASE_URL,
        }.items()
        if not value
    ]

    if missing:
        log.error(
            f"Missing required .env values: {', '.join(missing)}"
        )
        sys.exit(2)
