"""
Reply monitoring loop.

Continuously polls the inbox for replies to sent invitations, matches
them to candidates via token, and classifies them. Backend-agnostic -
see email_backend.py for the IMAP vs Gmail API switch.
"""

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
from email_backend import get_email_backend
from reply_classifier import classify_reply

log = logging.getLogger(__name__)


def check_for_replies(backend, pending_tokens: list) -> list:
    """
    Check the inbox for new replies and match them to candidates.

    Args:
        backend: Active email backend (see email_backend.py).
        pending_tokens (list): Tokens currently awaiting a reply.

    Returns:
        list: List of tokens that matched new replies.
    """
    matched_tokens = []

    for reply in backend.fetch_unseen(pending_tokens):
        token = reply["token"]

        # Verify sender
        expected_email = get_candidate_email(token)
        if expected_email.lower() not in reply["from"].lower():
            log.warning(
                f"Token {token} matched but "
                f"sender mismatch: "
                f"expected {expected_email}, "
                f"got {reply['from']}. "
                f"Recording anyway."
            )

        log.info(
            f"Reply detected | "
            f"token={token} | "
            f"from={reply['from']} | "
            f"subject='{reply['subject']}'"
        )

        record_reply(
            token,
            reply["subject"],
            reply["body"],
            datetime.now(timezone.utc),
        )

        matched_tokens.append(token)

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

    backend = get_email_backend()
    backend.start()
    start_time = time.time()
    timeout_seconds = MAX_MONITOR_MINUTES * 60

    try:
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
            matched = check_for_replies(backend, still_pending)

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

    finally:
        backend.stop()
