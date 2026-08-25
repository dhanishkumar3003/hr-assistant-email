"""
Reply classification logic.

Classifies candidate replies as interested, declined, or needing review.
Currently uses rule-based classification; can be replaced with ML/LLM.
"""

import logging

log = logging.getLogger(__name__)

# Classification result constants
CLASSIFICATION_INTERESTED = "interested"
CLASSIFICATION_DECLINED = "declined"
CLASSIFICATION_NEEDS_REVIEW = "needs_review"


def classify_reply(body: str) -> str:
    """
    Classify a candidate reply based on email body content.
    
    Temporary rule-based classifier. Can be replaced by Ollama
    or other ML models in the future.
    
    Args:
        body (str): Email body text.
    
    Returns:
        str: Classification: 'interested', 'declined', or 'needs_review'.
    """
    text = (body or "").lower()
    
    # Check for decline keywords
    if (
        "not interested" in text
        or "decline" in text
    ):
        return CLASSIFICATION_DECLINED
    
    # Check for interest keywords
    if (
        "interested" in text
        or "yes" in text
    ):
        return CLASSIFICATION_INTERESTED
    
    # Default to manual review
    return CLASSIFICATION_NEEDS_REVIEW
