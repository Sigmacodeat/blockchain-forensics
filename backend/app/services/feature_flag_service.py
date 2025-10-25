"""
Enterprise Feature-Flag-System
LaunchDarkly-Style Feature Management mit A/B-Testing Support
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import hashlib
import json
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


class FeatureFlagStatus(str, Enum):
    """Feature Flag Status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ROLLOUT = "rollout"  # Gradual rollout
    AB_TEST = "ab_test"  # A/B Testing


class FeatureFlag:
    """Feature Flag Model"""
    
    def __init__(
        self,
        key: str,
        name: str,
        description: str,
        status: FeatureFlagStatus = FeatureFlagStatus.DISABLED,
        rollout_percentage: int = 0,
        rollout_user_ids: Optional[List[str]] = None,
        environment: str = "production",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.key = key
        self.name = name
        self.description = description
        self.status = status
        self.rollout_percentage = rollout_percentage
        self.rollout_user_ids = rollout_user_ids or []
        self.environment = environment
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "rollout_percentage": self.rollout_percentage,
            "rollout_user_ids": self.rollout_user_ids,
            "environment": self.environment,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlag":
        """Create from dictionary"""
        return cls(
            key=data["key"],
            name=data["name"],
            description=data["description"],
            status=FeatureFlagStatus(data["status"]),
            rollout_percentage=data.get("rollout_percentage", 0),
            rollout_user_ids=data.get("rollout_user_ids", []),
            environment=data.get("environment", "production"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )


class FeatureFlagService:
    """Enterprise Feature-Flag Service"""
    
    def __init__(self):
        self.redis_prefix = "feature_flag:"
        self.ttl = 3600  # 1 hour cache
    
    def _get_redis_key(self, flag_key: str) -> str:
        """Get Redis key for feature flag"""
        return f"{self.redis_prefix}{flag_key}"
    
    def _calculate_user_bucket(self, user_id: str, flag_key: str) -> int:
        """
        Calculate user bucket (0-99) for consistent rollout
        Same user always gets same bucket for same flag
        """
        combined = f"{user_id}:{flag_key}"
        hash_obj = hashlib.md5(combined.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        return hash_int % 100
    
    async def create_flag(
        self,
        key: str,
        name: str,
        description: str,
        status: FeatureFlagStatus = FeatureFlagStatus.DISABLED
    ) -> FeatureFlag:
        """Create a new feature flag"""
        try:
            # Check if flag already exists
            existing = await self.get_flag(key)
            if existing:
                raise ValueError(f"Feature flag '{key}' already exists")
            
            flag = FeatureFlag(
                key=key,
                name=name,
                description=description,
                status=status
            )
            
            # Store in Redis
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                redis_key = self._get_redis_key(key)
                await client.set(redis_key, json.dumps(flag.to_dict()))
            
            logger.info(f"Created feature flag: {key}")
            return flag
            
        except Exception as e:
            logger.error(f"Error creating feature flag {key}: {e}")
            raise
    
    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """Get feature flag by key"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if not client:
                return None
            
            redis_key = self._get_redis_key(key)
            data = await client.get(redis_key)
            
            if not data:
                return None
            
            flag_dict = json.loads(data)
            return FeatureFlag.from_dict(flag_dict)
            
        except Exception as e:
            logger.error(f"Error getting feature flag {key}: {e}")
            return None
    
    async def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if not client:
                return []
            
            # Get all keys matching prefix
            pattern = f"{self.redis_prefix}*"
            keys = await client.keys(pattern)
            
            flags = []
            for key in keys:
                data = await client.get(key)
                if data:
                    flag_dict = json.loads(data)
                    flags.append(FeatureFlag.from_dict(flag_dict))
            
            return flags
            
        except Exception as e:
            logger.error(f"Error listing feature flags: {e}")
            return []
    
    async def update_flag(
        self,
        key: str,
        status: Optional[FeatureFlagStatus] = None,
        rollout_percentage: Optional[int] = None,
        rollout_user_ids: Optional[List[str]] = None
    ) -> FeatureFlag:
        """Update feature flag"""
        try:
            flag = await self.get_flag(key)
            if not flag:
                raise ValueError(f"Feature flag '{key}' not found")
            
            # Update fields
            if status is not None:
                flag.status = status
            if rollout_percentage is not None:
                flag.rollout_percentage = max(0, min(100, rollout_percentage))
            if rollout_user_ids is not None:
                flag.rollout_user_ids = rollout_user_ids
            
            flag.updated_at = datetime.utcnow()
            
            # Save to Redis
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if client:
                redis_key = self._get_redis_key(key)
                await client.set(redis_key, json.dumps(flag.to_dict()))
            
            logger.info(f"Updated feature flag: {key}")
            return flag
            
        except Exception as e:
            logger.error(f"Error updating feature flag {key}: {e}")
            raise
    
    async def delete_flag(self, key: str) -> bool:
        """Delete feature flag"""
        try:
            await redis_client._ensure_connected()
            client = getattr(redis_client, "client", None)
            if not client:
                return False
            
            redis_key = self._get_redis_key(key)
            deleted = await client.delete(redis_key)
            
            logger.info(f"Deleted feature flag: {key}")
            return bool(deleted)
            
        except Exception as e:
            logger.error(f"Error deleting feature flag {key}: {e}")
            return False
    
    async def is_enabled(
        self,
        key: str,
        user_id: Optional[str] = None,
        default: bool = False
    ) -> bool:
        """
        Check if feature is enabled for user
        
        Logic:
        - ENABLED: Always true
        - DISABLED: Always false
        - ROLLOUT: True if user in percentage or explicit list
        - AB_TEST: True if user in A group (bucket < 50)
        """
        try:
            flag = await self.get_flag(key)
            if not flag:
                return default
            
            # Simple cases
            if flag.status == FeatureFlagStatus.ENABLED:
                return True
            if flag.status == FeatureFlagStatus.DISABLED:
                return False
            
            # Requires user_id for ROLLOUT and AB_TEST
            if not user_id:
                return default
            
            # Check explicit user list
            if user_id in flag.rollout_user_ids:
                return True
            
            # Percentage-based rollout
            if flag.status == FeatureFlagStatus.ROLLOUT:
                user_bucket = self._calculate_user_bucket(user_id, key)
                return user_bucket < flag.rollout_percentage
            
            # A/B Test (A group = bucket < 50)
            if flag.status == FeatureFlagStatus.AB_TEST:
                user_bucket = self._calculate_user_bucket(user_id, key)
                return user_bucket < 50
            
            return default
            
        except Exception as e:
            logger.error(f"Error checking feature flag {key}: {e}")
            return default
    
    async def get_variant(self, key: str, user_id: str) -> str:
        """
        Get A/B test variant for user
        Returns: 'A' or 'B'
        """
        try:
            flag = await self.get_flag(key)
            if not flag or flag.status != FeatureFlagStatus.AB_TEST:
                return 'A'  # Default variant
            
            user_bucket = self._calculate_user_bucket(user_id, key)
            return 'A' if user_bucket < 50 else 'B'
            
        except Exception as e:
            logger.error(f"Error getting variant for {key}: {e}")
            return 'A'


# Global instance
feature_flag_service = FeatureFlagService()
