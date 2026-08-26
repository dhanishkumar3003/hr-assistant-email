"""
Candidate state persistence.

Backed by PostgreSQL via SQLAlchemy (emails / candidate_responses
tables) instead of the old candidates_state.json file. Reply tracking
still keys off the token embedded in the email subject.
"""

import logging
from db import SessionLocal
from models import Email, CandidateResponse

log = logging.getLogger(__name__)

EMAIL_TYPE_INTERVIEW_INVITATION = "interview_invitation"
STATUS_SENT = "Sent"


def save_sent_email(
    token: str,
    candidate_email: str,
    candidate_name: str,
    subject: str,
    body: str,
    sent_at,
) -> None:
    """
    Record a newly sent invitation email.

    Args:
        token (str): Unique tracking token embedded in the subject.
        candidate_email (str): Candidate email address.
        candidate_name (str): Candidate name (can be empty).
        subject (str): Sent email subject.
        body (str): Sent email body.
        sent_at (datetime): Time the email was sent.
    """
    with SessionLocal() as session:
        session.add(
            Email(
                token=token,
                candidate_email=candidate_email,
                candidate_name=candidate_name,
                recipient_email=candidate_email,
                subject=subject,
                body=body,
                email_type=EMAIL_TYPE_INTERVIEW_INVITATION,
                status=STATUS_SENT,
                sent_at=sent_at,
            )
        )
        session.commit()
    log.debug(f"Saved sent email to DB | token={token}")


def get_pending_tokens() -> list:
    """
    Get tokens for sent emails that have no reply yet.

    Returns:
        list: Token strings.
    """
    with SessionLocal() as session:
        rows = (
            session.query(Email.token)
            .outerjoin(CandidateResponse, CandidateResponse.email_id == Email.email_id)
            .filter(CandidateResponse.response_id.is_(None))
            .all()
        )
        return [row.token for row in rows]


def get_candidate_email(token: str) -> str:
    """
    Get the expected candidate email address for a token.

    Args:
        token (str): Tracking token.

    Returns:
        str: Candidate email address, or None if token is unknown.
    """
    with SessionLocal() as session:
        email = session.query(Email).filter(Email.token == token).first()
        return email.candidate_email if email else None


def record_reply(token: str, subject: str, body: str, received_at) -> None:
    """
    Record a candidate's reply against its tracking token.

    Args:
        token (str): Tracking token from the reply subject.
        subject (str): Reply subject.
        body (str): Reply body text.
        received_at (datetime): Time the reply was received.
    """
    with SessionLocal() as session:
        email = session.query(Email).filter(Email.token == token).first()
        if not email:
            log.warning(f"record_reply called for unknown token={token}")
            return

        session.add(
            CandidateResponse(
                email_id=email.email_id,
                subject=subject,
                response_body=body,
                received_at=received_at,
            )
        )
        session.commit()


def get_reply_body(token: str) -> str:
    """
    Get the most recent unclassified reply body for a token.

    Args:
        token (str): Tracking token.

    Returns:
        str: Reply body text, or None if not found.
    """
    with SessionLocal() as session:
        response = (
            session.query(CandidateResponse)
            .join(Email, Email.email_id == CandidateResponse.email_id)
            .filter(Email.token == token, CandidateResponse.intent.is_(None))
            .order_by(CandidateResponse.received_at.desc())
            .first()
        )
        return response.response_body if response else None


def set_classification(token: str, classification: str, analyzed_at) -> None:
    """
    Store the classification result for a candidate's reply.

    Args:
        token (str): Tracking token.
        classification (str): Result from reply_classifier.classify_reply().
        analyzed_at (datetime): Time the classification ran.
    """
    with SessionLocal() as session:
        response = (
            session.query(CandidateResponse)
            .join(Email, Email.email_id == CandidateResponse.email_id)
            .filter(Email.token == token, CandidateResponse.intent.is_(None))
            .order_by(CandidateResponse.received_at.desc())
            .first()
        )
        if not response:
            log.warning(f"set_classification called for unknown token={token}")
            return

        response.intent = classification
        response.analyzed_at = analyzed_at
        session.commit()
