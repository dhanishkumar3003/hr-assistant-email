"""Gmail API operations used by sending and reply monitoring."""

import base64
import logging
from email.message import EmailMessage
from gmail_auth import get_gmail_service

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
