"""
Email sending operations for inviting candidates.

Sends invitation emails and tracks them in state.
"""

import logging
from datetime import datetime, timezone
from config import require_config
from state_manager import load_state, save_state, create_candidate_record
from token_manager import generate_token
from email_handler import build_invite_message
from gmail_client import send_message

log = logging.getLogger(__name__)


def send_invite(to_addr: str, candidate_name: str = "") -> str:
    """
    Send an invitation email to a candidate and save state.
    
    Generates a unique tracking token, embeds it in the email subject,
    sends via Gmail SMTP, and records the candidate in state.
    
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
    
    # Send via SMTP
    if not send_message(message):
        return None
    
    log.info(
        f"Sent invite to {to_addr} | "
        f"token={token} | "
        f"subject='{subject}'"
    )
    
    # Save to state
    state = load_state()
    sent_at = datetime.now(timezone.utc).isoformat()
    
    state[token] = create_candidate_record(
        to_addr,
        candidate_name,
        sent_at,
        token
    )
    
    save_state(state)
    
    return token
