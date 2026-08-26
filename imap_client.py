"""
IMAP/SMTP email backend - the original polling mechanism.

send_message/connect_to_inbox/disconnect_inbox are unchanged from
before the Gmail API work started. ImapBackend just adapts them to the
common backend interface (see email_backend.py) so monitor.py/sender.py
can switch to gmail_client.GmailApiBackend without any changes.
"""

import smtplib
import imaplib
import logging
from email.message import EmailMessage
from config import (
    GMAIL_ADDRESS,
    GMAIL_APP_PASSWORD,
    GMAIL_SMTP_SERVER,
    GMAIL_IMAP_SERVER,
    GMAIL_SMTP_PORT,
)
from email_handler import match_reply

log = logging.getLogger(__name__)


def send_message(message: EmailMessage) -> bool:
    """
    Send an email message via Gmail SMTP.

    Args:
        message (EmailMessage): Email message to send.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with smtplib.SMTP(
            GMAIL_SMTP_SERVER,
            GMAIL_SMTP_PORT,
            timeout=20
        ) as smtp:
            smtp.starttls()
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.send_message(message)

        log.debug(f"Message sent to {message['To']}")
        return True

    except Exception as e:
        log.error(f"SMTP send failed for {message['To']}: {e!r}")
        return False


def connect_to_inbox() -> imaplib.IMAP4_SSL:
    """
    Connect to Gmail IMAP inbox.

    Returns:
        imaplib.IMAP4_SSL: Connected IMAP object.

    Raises:
        imaplib.IMAP4.error: If connection fails.
    """
    try:
        mail = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER)
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        mail.select("INBOX")
        log.info("Connected to Gmail inbox.")
        return mail

    except Exception as e:
        log.error(f"Failed to connect to Gmail IMAP: {e!r}")
        raise


def disconnect_inbox(mail: imaplib.IMAP4_SSL) -> None:
    """
    Safely disconnect from IMAP inbox.

    Args:
        mail (imaplib.IMAP4_SSL): IMAP connection object.
    """
    try:
        mail.logout()
        log.debug("Disconnected from IMAP.")
    except Exception as e:
        log.warning(f"Error disconnecting from IMAP: {e!r}")


class ImapBackend:
    """Email backend using SMTP send + IMAP polling."""

    def __init__(self):
        self._mail = None

    def start(self) -> None:
        """Open the IMAP connection used for the whole monitoring loop."""
        self._mail = connect_to_inbox()

    def send(self, message: EmailMessage) -> bool:
        """Send an email via SMTP."""
        return send_message(message)

    def fetch_unseen(self, pending_tokens: list) -> list:
        """
        Fetch unseen inbox messages matching a pending token.

        Fetching a message's RFC822 body marks it \\Seen server-side,
        so no separate mark-as-read step is needed (matches the
        original behavior).

        Args:
            pending_tokens (list): Tokens currently awaiting a reply.

        Returns:
            list: Matching replies as {"token", "subject", "from", "body"}.
        """
        status, messages = self._mail.search(None, "UNSEEN")

        if status != "OK":
            log.warning("IMAP search failed.")
            return []

        message_ids = messages[0].split()
        matches = []

        for message_id in message_ids:
            status, msg_data = self._mail.fetch(message_id, "(RFC822)")

            if status != "OK":
                continue

            match = match_reply(msg_data[0][1], pending_tokens)
            if match:
                matches.append(match)

        self._mail.select("INBOX")
        return matches

    def stop(self) -> None:
        """Close the IMAP connection."""
        if self._mail:
            disconnect_inbox(self._mail)
