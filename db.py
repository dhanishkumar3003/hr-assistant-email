"""
Database engine and session setup.

SQLAlchemy engine bound to DATABASE_URL, plus a session factory used
by state_manager.py for all persistence.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
