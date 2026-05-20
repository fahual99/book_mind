"""
Database connection module using SQLAlchemy + SQLite.
Handles session management and database initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
DB_PATH = os.path.join(DB_DIR, "book_recommender.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from .models import User, Favorite  # noqa: F401
    Base.metadata.create_all(bind=engine)
