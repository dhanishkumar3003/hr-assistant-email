"""
Reply monitoring loop.

Continuously polls Gmail inbox for replies to sent invitations,
matches them to candidates via token, extracts body, and classifies.
"""

import time
import logging
from datetime import datetime, timezone
from config import (
    require_config,
    POLL_INTERVAL_SECONDS,
    MAX_MONITOR_MINUTES,
)
from state_manager import load_state, save_state, get_pending_tokens
from gmail_client import connect_to_inbox, disconnect_inbox
from token_manager import extract_token
from email_handler import get_email_body, parse_email_bytes
from reply_classifier import classify_reply

log = logging.getLogger(__name__)


def check_for_replies(mail, state: dict) -> list:
    """
    Check Gmail inbox for new replies and match them to candidates.
    
    Searches for unseen emails, extracts tracking tokens, verifies
    sender matches expected candidate, and updates state with reply.
    
    Args:
        mail: Connected IMAP object.
        state (dict): Current candidate state.
    
    Returns:
        list: List of tokens that matched new replies.
    """
    status, messages = mail.search(None, "UNSEEN")
    
    if status != "OK":
        log.warning("IMAP search failed.")
        return []
    
    message_ids = messages[0].split()
    
    if not message_ids:
        return []
    
    matched_tokens = []
    
    for message_id in message_ids:
        status, msg_data = mail.fetch(message_id, "(RFC822)")
        
        if status != "OK":
            continue
        
        raw_email = msg_data[0][1]
        email_info = parse_email_bytes(raw_email)
        
        # Extract token from subject
        token = extract_token(email_info["subject"])
        
        if not token or token not in state:
            continue
        
        record = state[token]
        
        # Verify sender
        if (
            record["candidate_email"].lower()
            not in email_info["from"].lower()
        ):
            log.warning(
                f"Token {token} matched but "
                f"sender mismatch: "
                f"expected {record['candidate_email']}, "
                f"got {email_info['from']}. "
                f"Recording anyway."
            )
        
        # Extract body
        body = get_email_body(email_info["msg"])
        
        log.info(
            f"Reply detected | "
            f"token={token} | "
            f"from={email_info['from']} | "
            f"subject='{email_info['subject']}'"
        )
        
        # Update state
        record["status"] = "replied"
        record["reply_body"] = body
        record["replied_at"] = datetime.now(timezone.utc).isoformat()
        
        matched_tokens.append(token)
    
    if matched_tokens:
        save_state(state)
    
    return matched_tokens


def monitor_replies() -> None:
    """
    Run the main monitoring loop.
    
    Continuously checks for replies to pending invitations,
    classifies them, and updates state. Runs until all candidates
    have replied or timeout is reached.
    """
    require_config()
    
    state = load_state()
    pending_tokens = get_pending_tokens(state)
    
    if not pending_tokens:
        log.info(
            "No pending candidates to monitor "
            "(nothing with status='sent')."
        )
        return
    
    log.info(
        f"Monitoring {len(pending_tokens)} "
        f"pending candidate(s) for replies..."
    )
    
    mail = connect_to_inbox()
    start_time = time.time()
    timeout_seconds = MAX_MONITOR_MINUTES * 60
    
    try:
        while True:
            state = load_state()
            still_pending = get_pending_tokens(state)
            
            if not still_pending:
                log.info(
                    "All tracked candidates have replied. Done."
                )
                break
            
            if time.time() - start_time > timeout_seconds:
                log.warning(
                    f"Monitor timeout reached "
                    f"({MAX_MONITOR_MINUTES} min). "
                    f"Still pending: {still_pending}"
                )
                break
            
            # Check for replies
            matched = check_for_replies(mail, state)
            
            # Classify new replies
            if matched:
                state = load_state()
                
                for token in matched:
                    record = state[token]
                    classification = classify_reply(record["reply_body"])
                    record["classification"] = classification
                    record["status"] = "classified"
                    
                    log.info(
                        f"Classified token={token} "
                        f"as '{classification}'"
                    )
                
                save_state(state)
            else:
                log.info(
                    f"No new replies. "
                    f"Checking again in {POLL_INTERVAL_SECONDS}s..."
                )
            
            time.sleep(POLL_INTERVAL_SECONDS)
            mail.select("INBOX")
    
    finally:
        disconnect_inbox(mail)
