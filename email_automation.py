#!/usr/bin/env python3

"""
Recruiting email sender + reply monitor (Gmail SMTP/IMAP).

Sends invite emails to one or more candidates with a unique tracking
token embedded in the subject line, then polls the inbox for replies
and matches them back to the correct candidate using that token.

This module orchestrates the CLI by importing modular components.

Usage:

    Single candidate:
        python email_automation.py send --to candidate@example.com

    Multiple candidates:
        python email_automation.py send --to candidate1@example.com candidate2@example.com

    With candidate name:
        python email_automation.py send --to candidate1@example.com --name "Jane Doe"

    Monitor replies:
        python email_automation.py monitor
"""

import sys
import logging
from cli import main

# ==================================================
# LOGGING SETUP
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("recruiting_mailer.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

log = logging.getLogger(__name__)


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Program interrupted by user.")
        sys.exit(0)
    except Exception as e:
        log.error(f"Unexpected error: {e!r}")
        sys.exit(1)