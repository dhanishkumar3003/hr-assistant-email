"""
Gmail API email backend.

send_message/list_unread_messages/mark_as_read are the raw Gmail API
operations. GmailApiBackend adapts them to the common backend interface
(see email_backend.py) so monitor.py/sender.py can switch to this
backend from imap_client.ImapBackend without any changes.
"""

import base64
import logging
from email.message import EmailMessage
from gmail_auth import get_gmail_service
from email_handler import match_reply

log = logging.getLogger(__name__)


def send_message(message: EmailMessage) -> bool:
    """
    Send an email message through the Gmail API.
    
    Args:
        message (EmailMessage): Email message to send.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("ascii")
        get_gmail_service().users().messages().send(
            userId="me",
            body={"raw": raw_message},
        ).execute()
        
        log.debug(f"Message sent to {message['To']}")
        return True
    
    except Exception as e:
        log.error(f"Gmail API send failed for {message['To']}: {e!r}")
        return False

def list_unread_messages() -> list[dict]:
    """
    Return unread inbox messages with their raw email contents.
    
    Returns:
        list[dict]: Gmail API message resources containing raw content.
    
    Raises:
        Exception: If the Gmail API request fails.
    """
    service = get_gmail_service()
    response = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        q="is:unread",
        maxResults=100,
    ).execute()
    return [
        service.users().messages().get(
            userId="me",
            id=message["id"],
            format="raw",
        ).execute()
        for message in response.get("messages", [])
    ]


def mark_as_read(message_id: str) -> None:
    """
    Remove the unread label after a message has been processed.
    """
    get_gmail_service().users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()


class GmailApiBackend:
    """Email backend using the Gmail API for both send and polling."""

    def start(self) -> None:
        """No persistent connection needed - each call fetches its own service."""

    def send(self, message: EmailMessage) -> bool:
        """Send an email via the Gmail API."""
        return send_message(message)

    def fetch_unseen(self, pending_tokens: list) -> list:
        """
        Fetch unread inbox messages matching a pending token.

        Args:
            pending_tokens (list): Tokens currently awaiting a reply.

        Returns:
            list: Matching replies as {"token", "subject", "from", "body"}.
        """
        matches = []

        for gmail_message in list_unread_messages():
            raw_email = base64.urlsafe_b64decode(gmail_message["raw"])
            match = match_reply(raw_email, pending_tokens)
            if match:
                matches.append(match)
                mark_as_read(gmail_message["id"])

        return matches

    def stop(self) -> None:
        """No persistent connection to close."""
