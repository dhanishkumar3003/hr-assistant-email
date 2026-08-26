"""
SQLAlchemy ORM models for the emails / candidate_responses tables.

Mirrors db/schema.sql. See that file for the token/candidate_email/
candidate_name note - fields added beyond the PDD schema because this
project matches replies via a subject-embedded token, not Module 1
candidate records.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
)
from sqlalchemy.sql import func
from db import Base


class Email(Base):
    __tablename__ = "emails"

    email_id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, nullable=True)
    token = Column(String(20), nullable=False, unique=True)
    candidate_email = Column(String(255), nullable=False)
    candidate_name = Column(String(255), nullable=True)
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    email_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    response_due_at = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    resend_count = Column(Integer, nullable=False, default=0)
    last_resent_at = Column(DateTime, nullable=True)
    next_resend_at = Column(DateTime, nullable=True)
    resend_reason = Column(String(100), nullable=True)
    is_resend = Column(Boolean, nullable=False, default=False)


class CandidateResponse(Base):
    __tablename__ = "candidate_responses"

    response_id = Column(Integer, primary_key=True)
    email_id = Column(Integer, ForeignKey("emails.email_id"), nullable=False)
    subject = Column(String(500), nullable=False)
    response_body = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    intent_percentage = Column(Numeric(5, 2), nullable=True)
    received_at = Column(DateTime, nullable=False)
    analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    candidate_requested_date = Column(DateTime, nullable=True)
    trigger_date = Column(DateTime, nullable=True)
    follow_up_required = Column(Boolean, nullable=False, default=False)
