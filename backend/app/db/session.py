"""
SQLAlchemy Session Configuration
================================

Database session management for the blockchain forensics platform.
Provides session factory for PostgreSQL with proper connection handling.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.config import settings

# Database URL - always use application settings to avoid mismatched environments
DATABASE_URL = settings.POSTGRES_URL

# Use SQLite for tests if TEST_MODE is enabled
if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
    DATABASE_URL = "sqlite:///./test_forensics.db"

# Create engine with appropriate settings
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False,  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test database setup for test mode
if os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
    # Import all models to create tables
    try:
        from app.models.case import Base as CaseBase
        from app.models.comment import Base as CommentBase
        from app.models.notification import Base as NotificationBase
        from app.models.user import Base as UserBase
        from app.models.vasp_risk_record import VaspRiskRecordORM

        # Create tables in test database
        CaseBase.metadata.create_all(bind=engine)
        CommentBase.metadata.create_all(bind=engine)
        NotificationBase.metadata.create_all(bind=engine)
        UserBase.metadata.create_all(bind=engine)
        VaspRiskRecordORM.__table__.create(bind=engine, checkfirst=True)
    except Exception as e:
        print(f"Warning: Could not create test database tables: {e}")

def get_db() -> Session:
    """
    Dependency function to get database session.
    Use this in FastAPI routes that need database access.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """
    Get a database session for use in services.
    Remember to close the session after use.
    """
    return SessionLocal()

# Health check function
def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception:
        return False
