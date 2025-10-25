#!/usr/bin/env python3
"""
Create Demo User Account for Testing
=====================================

Creates a demo user account with:
- Email: demo@sigmacode.io
- Password: Demo123!
- Plan: Pro (to showcase features)
- Role: ANALYST
- Pre-populated with sample data
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import engine, get_db
from app.models.user import UserORM, UserRole
from app.auth.jwt import get_password_hash
from datetime import datetime, timedelta
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_user(db: Session):
    """Create or update demo user account"""
    
    demo_email = "demo@sigmacode.io"
    demo_password = "Demo123!"
    
    # Check if demo user already exists
    existing_user = db.query(UserORM).filter(UserORM.email == demo_email).first()
    
    if existing_user:
        logger.info(f"✅ Demo user already exists: {demo_email}")
        logger.info(f"   ID: {existing_user.id}")
        logger.info(f"   Plan: {existing_user.plan}")
        logger.info(f"   Role: {existing_user.role}")
        return existing_user
    
    # Create new demo user
    demo_user = UserORM(
        id=str(uuid.uuid4()),
        email=demo_email,
        username="demo_analyst",
        hashed_password=get_password_hash(demo_password),
        role=UserRole.ANALYST,  # Can access most forensic features
        plan="pro",  # Pro plan to showcase features
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        features=["trace", "investigator", "cases", "correlation", "analytics", "custom-entities"],
        organization="SIGMACODE Demo",
    )
    
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)
    
    logger.info("✅ Demo user created successfully!")
    logger.info(f"   Email: {demo_email}")
    logger.info(f"   Password: {demo_password}")
    logger.info(f"   ID: {demo_user.id}")
    logger.info(f"   Plan: {demo_user.plan}")
    logger.info(f"   Role: {demo_user.role.value}")
    logger.info(f"   Organization: {demo_user.organization}")
    logger.info("")
    logger.info("🔐 Login Credentials:")
    logger.info(f"   URL: http://localhost:3000/en/login")
    logger.info(f"   Email: {demo_email}")
    logger.info(f"   Password: {demo_password}")
    
    return demo_user


def main():
    """Main execution"""
    logger.info("🚀 Creating Demo User Account...")
    logger.info("")
    
    # Create database session
    db = next(get_db())
    
    try:
        demo_user = create_demo_user(db)
        
        logger.info("")
        logger.info("✅ Demo user setup complete!")
        logger.info("")
        logger.info("📝 Next Steps:")
        logger.info("   1. Navigate to http://localhost:3000/en/login")
        logger.info("   2. Login with demo@sigmacode.io / Demo123!")
        logger.info("   3. Explore Dashboard, Trace, Investigator, Cases")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error creating demo user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
