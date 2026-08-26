"""
Email backend selector.

Two interchangeable backends, both exposing the same interface
(start, send, fetch_unseen, stop):
  - imap_client.ImapBackend  - SMTP send + IMAP polling (the original
    mechanism, unchanged).
  - gmail_client.GmailApiBackend - Gmail API send + Gmail API polling,
    authenticated via gmail_auth.py.

Selected by EMAIL_BACKEND in .env ("imap" or "gmail_api"). monitor.py
and sender.py only depend on this module, never on a specific backend,
so switching is a one-line .env change.
"""

from config import EMAIL_BACKEND


def get_email_backend():
    """
    Build the configured email backend.

    Returns:
        ImapBackend or GmailApiBackend, per EMAIL_BACKEND.
    """
    if EMAIL_BACKEND == "gmail_api":
        from gmail_client import GmailApiBackend
        return GmailApiBackend()

    from imap_client import ImapBackend
    return ImapBackend()
