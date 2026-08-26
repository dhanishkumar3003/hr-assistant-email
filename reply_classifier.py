"""
Reply classification logic.

Classifies candidate replies as interested, declined, or needing review.
Rule-based phrase matching handles the common ways candidates actually
reply to interview invitations; anything ambiguous falls through to the
Ollama-hosted LLM classifier (llm_reply_classifier.py) before finally
defaulting to manual review.
"""

import re
import logging
from config import (
    REPLY_AUTO_REPLY_PATTERNS,
    REPLY_DECLINED_PATTERNS,
    REPLY_INTERESTED_PATTERNS,
)

log = logging.getLogger(__name__)

# Classification result constants
CLASSIFICATION_INTERESTED = "interested"
CLASSIFICATION_DECLINED = "declined"
CLASSIFICATION_NEEDS_REVIEW = "needs_review"

# Maps llm_reply_classifier's labels onto the constants above
_LLM_LABEL_TO_CLASSIFICATION = {
    "INTERESTED": CLASSIFICATION_INTERESTED,
    "NOT_INTERESTED": CLASSIFICATION_DECLINED,
    "OTHER": CLASSIFICATION_NEEDS_REVIEW,
}


def classify_reply(body: str) -> str:
    """
    Classify a candidate reply based on email body content.

    Phrase-based matching handles common interview-reply patterns first;
    anything that doesn't match is sent to the LLM classifier before
    falling back to needs_review.

    Args:
        body (str): Email body text.

    Returns:
        str: Classification: 'interested', 'declined', or 'needs_review'.
    """
    text = (body or "").lower()

    if _matches_any(text, REPLY_AUTO_REPLY_PATTERNS):
        return CLASSIFICATION_NEEDS_REVIEW

    if _matches_any(text, REPLY_DECLINED_PATTERNS):
        return CLASSIFICATION_DECLINED

    if _matches_any(text, REPLY_INTERESTED_PATTERNS):
        return CLASSIFICATION_INTERESTED

    # Ambiguous - ask the LLM before giving up to manual review
    return _classify_with_llm(body)


def _matches_any(text: str, patterns: list) -> bool:
    """Return True if any regex pattern matches text."""
    return any(re.search(pattern, text) for pattern in patterns)


def _classify_with_llm(body: str) -> str:
    """
    Fall back to the Ollama LLM classifier for ambiguous replies.

    Args:
        body (str): Email body text.

    Returns:
        str: Mapped classification, or needs_review if the LLM is
            unavailable or returns an unrecognized label.
    """
    try:
        from llm_reply_classifier import classify_reply_llm
        label = classify_reply_llm(body)
    except Exception as exc:
        log.warning(
            f"LLM classification unavailable, defaulting to "
            f"needs_review: {exc}"
        )
        return CLASSIFICATION_NEEDS_REVIEW

    return _LLM_LABEL_TO_CLASSIFICATION.get(label, CLASSIFICATION_NEEDS_REVIEW)
