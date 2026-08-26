"""
Reply monitoring loop.

Continuously polls Gmail inbox for replies to sent invitations,
matches them to candidates via token, extracts body, and classifies.
"""

import base64
import time
import logging
from datetime import datetime, timezone
from config import (
    require_config,
    POLL_INTERVAL_SECONDS,
    MAX_MONITOR_MINUTES,
)
from state_manager import (
    get_pending_tokens,
    get_candidate_email,
    record_reply,
    get_reply_body,
    set_classification,
)
from gmail_client import list_unread_messages, mark_as_read
from token_manager import extract_token
from email_handler import get_email_body, parse_email_bytes
from reply_classifier import classify_reply

log = logging.getLogger(__name__)


def check_for_replies(pending_tokens: list) -> list:
    """
    Check Gmail inbox for new replies and match them to candidates.

    Searches for unseen emails, extracts tracking tokens, verifies
    sender matches expected candidate, and records the reply in the DB.

    Args:
        pending_tokens (list): Tokens currently awaiting a reply.

    Returns:
        list: List of tokens that matched new replies.
    """
    messages = list_unread_messages()
    if not messages:
        return []

    matched_tokens = []

    for message in messages:
        raw_email = base64.urlsafe_b64decode(message["raw"])
        email_info = parse_email_bytes(raw_email)

        # Extract token from subject
        token = extract_token(email_info["subject"])

        if not token or token not in pending_tokens:
            continue

        # Verify sender
        expected_email = get_candidate_email(token)
        if expected_email.lower() not in email_info["from"].lower():
            log.warning(
                f"Token {token} matched but "
                f"sender mismatch: "
                f"expected {expected_email}, "
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

        record_reply(
            token,
            email_info["subject"],
            body,
            datetime.now(timezone.utc),
        )

        matched_tokens.append(token)
        mark_as_read(message["id"])

    return matched_tokens


def monitor_replies() -> None:
    """
    Run the main monitoring loop.
    
    Continuously checks for replies to pending invitations,
    classifies them, and updates state. Runs until all candidates
    have replied or timeout is reached.
    """
    require_config()

    pending_tokens = get_pending_tokens()

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
    
    start_time = time.time()
    timeout_seconds = MAX_MONITOR_MINUTES * 60
    
    while True:
        still_pending = get_pending_tokens()

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
        matched = check_for_replies(still_pending)

        # Classify new replies
        if matched:
            for token in matched:
                reply_body = get_reply_body(token)
                classification = classify_reply(reply_body)
                set_classification(
                    token, classification, datetime.now(timezone.utc)
                )

                log.info(
                    f"Classified token={token} "
                    f"as '{classification}'"
                )
        else:
            log.info(
                f"No new replies. "
                f"Checking again in {POLL_INTERVAL_SECONDS}s..."
            )

        time.sleep(POLL_INTERVAL_SECONDS)
