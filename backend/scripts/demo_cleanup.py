#!/usr/bin/env python3
"""
Demo Cleanup CRON Script
=========================

Runs every 5 minutes to clean up expired demo users.

Usage:
  python scripts/demo_cleanup.py

CRON Setup:
  */5 * * * * cd /path/to/backend && python scripts/demo_cleanup.py >> /var/log/demo_cleanup.log 2>&1
"""

import sys
import os
from pathlib import Path
import asyncio
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.demo_service import demo_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main execution"""
    logger.info("🧹 Starting demo cleanup...")
    
    try:
        # Run cleanup
        count = await demo_service.cleanup_expired_demos()
        
        if count > 0:
            logger.info(f"✅ Cleaned up {count} expired demo accounts")
        else:
            logger.info("✅ No expired demos to clean up")
        
        # Get stats
        stats = await demo_service.get_demo_stats()
        logger.info(f"📊 Current stats: {stats}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
