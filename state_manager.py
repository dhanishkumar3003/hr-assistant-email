"""
State management for candidate tracking.

Handles loading and saving candidate state (sent emails,
replies, classifications) to/from JSON file.
"""

import os
import json
import logging
from config import STATE_FILE

log = logging.getLogger(__name__)


def load_state() -> dict:
    """
    Load candidate state from disk.
    
    Returns:
        dict: State dictionary, or empty dict if file doesn't exist.
    """
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    """
    Save candidate state to disk.
    
    Args:
        state (dict): State dictionary to persist.
    """
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    log.debug(f"State saved to {STATE_FILE}")


def get_pending_tokens(state: dict) -> list:
    """
    Get all tokens with 'sent' status (awaiting replies).
    
    Args:
        state (dict): Current state dictionary.
    
    Returns:
        list: List of token strings.
    """
    return [
        token
        for token, record in state.items()
        if record["status"] == "sent"
    ]


def create_candidate_record(
    to_addr: str,
    candidate_name: str,
    sent_at: str,
    token: str
) -> dict:
    """
    Create a new candidate record.
    
    Args:
        to_addr (str): Candidate email address.
        candidate_name (str): Candidate name.
        sent_at (str): ISO format timestamp.
        token (str): Unique tracking token.
    
    Returns:
        dict: Candidate record.
    """
    return {
        "candidate_email": to_addr,
        "candidate_name": candidate_name,
        "sent_at": sent_at,
        "status": "sent",
        "reply_body": None,
        "classification": None,
        "replied_at": None,
    }
