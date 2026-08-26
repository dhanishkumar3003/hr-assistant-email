"""
Email message building and parsing.

Handles construction of invitation emails and extraction
of text content from received emails.
"""

import email
import logging
from email.message import EmailMessage
from config import GMAIL_ADDRESS
from token_manager import extract_token

log = logging.getLogger(__name__)


def build_invite_message(
    to_addr: str,
    candidate_name: str,
    subject: str
) -> EmailMessage:
    """
    Build an invitation email message.
    
    Args:
        to_addr (str): Recipient email address.
        candidate_name (str): Name to use in greeting (can be empty).
        subject (str): Email subject line with tracking token.
    
    Returns:
        EmailMessage: Constructed email message.
    """
    greeting = (
        f"Hi {candidate_name},"
        if candidate_name
        else "Hi,"
    )
    
    body = f"""
{greeting}

We'd like to invite you to the next stage of our recruitment process.

Please reply to this email to confirm your interest, and let us know
your availability for a short interview.

Thank you,

Recruiting Team
"""
    
    message = EmailMessage()
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_addr
    message["Subject"] = subject
    message.set_content(body)
    
    return message


def get_email_body(msg) -> str:
    """
    Extract plain text body from email message.
    
    Handles both multipart and simple emails, preferring
    plain text content and skipping attachments.
    
    Args:
        msg: Email message object from email.message_from_bytes().
    
    Returns:
        str: Plain text body content, or empty string if none found.
    """
    if msg.is_multipart():
        # For multipart emails, find the plain text part
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if (
                content_type == "text/plain"
                and "attachment" not in content_disposition
            ):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="ignore")
        
        return ""
    
    # For simple emails, extract payload directly
    payload = msg.get_payload(decode=True)
    return (
        payload.decode(errors="ignore")
        if payload
        else ""
    )


def parse_email_bytes(raw_email: bytes) -> dict:
    """
    Parse raw email bytes into a structured message.
    
    Args:
        raw_email (bytes): Raw email data.
    
    Returns:
        dict: Dictionary with 'msg' (email message object),
              'from' (sender), and 'subject' keys.
    """
    msg = email.message_from_bytes(raw_email)
    return {
        "msg": msg,
        "from": msg.get("From", ""),
        "subject": msg.get("Subject", ""),
    }


def match_reply(raw_email: bytes, pending_tokens: list) -> dict:
    """
    Parse a raw email and check whether it replies to a pending token.

    Shared by every email backend (imap_client.py, gmail_client.py) so
    the token/pending-list matching logic isn't duplicated per backend.

    Args:
        raw_email (bytes): Raw email data.
        pending_tokens (list): Tokens currently awaiting a reply.

    Returns:
        dict: {"token", "subject", "from", "body"} if this email matches
            a pending token, otherwise None.
    """
    email_info = parse_email_bytes(raw_email)
    token = extract_token(email_info["subject"])

    if not token or token not in pending_tokens:
        return None

    return {
        "token": token,
        "subject": email_info["subject"],
        "from": email_info["from"],
        "body": get_email_body(email_info["msg"]),
    }
