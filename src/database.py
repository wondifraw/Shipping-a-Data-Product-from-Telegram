"""
database.py
-----------
Database connection utilities for SQLAlchemy. Provides engine, session, and helper functions for database access.
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Yield a database session and ensure it is closed after use. Handles exceptions during session creation and closing."""
    try:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        print(f"Error in get_db: {e}")

def get_engine():
    """Return the SQLAlchemy engine instance. Handles exceptions during engine retrieval."""
    try:
        return engine
    except Exception as e:
        print(f"Error in get_engine: {e}")
        return None