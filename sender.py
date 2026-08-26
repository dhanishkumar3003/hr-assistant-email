"""
Email sending operations for inviting candidates.

Sends invitation emails and tracks them in state.
"""

import logging
from datetime import datetime, timezone
from config import require_config
from state_manager import save_sent_email
from token_manager import generate_token
from email_handler import build_invite_message
from email_backend import get_email_backend

log = logging.getLogger(__name__)


def send_invite(to_addr: str, candidate_name: str = "") -> str:
    """
    Send an invitation email to a candidate and save state.
    
    Generates a unique tracking token, embeds it in the email subject,
    sends via the configured backend, and records the candidate in state.
    
    Args:
        to_addr (str): Candidate email address.
        candidate_name (str): Candidate name (optional).
    
    Returns:
        str: Tracking token if successful, None if sending failed.
    """
    require_config()
    
    # Generate tracking token
    token = generate_token()
    subject = f"Interview Invitation [Ref:{token}]"
    
    # Build email message
    message = build_invite_message(to_addr, candidate_name, subject)

    # Send via the configured backend (imap or gmail_api)
    if not get_email_backend().send(message):
        return None
    
    log.info(
        f"Sent invite to {to_addr} | "
        f"token={token} | "
        f"subject='{subject}'"
    )

    # Save to database
    sent_at = datetime.now(timezone.utc)

    save_sent_email(
        token,
        to_addr,
        candidate_name,
        subject,
        message.get_content(),
        sent_at,
    )

    return token
