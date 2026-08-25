"""
Gmail client for SMTP and IMAP operations.

Provides wrapper functions for sending emails via SMTP
and reading emails via IMAP.
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
