from __future__ import annotations
import os
import json
from typing import Optional, Dict, Any

try:
    from confluent_kafka.schema_registry import SchemaRegistryClient
    from confluent_kafka.schema_registry.avro import AvroSchema
    _HAS_SR = True
except Exception:
    SchemaRegistryClient = None  # type: ignore
    AvroSchema = None  # type: ignore
    _HAS_SR = False

from app.config import settings
try:
    from app.schemas.canonical_event import CanonicalEventAvroSchema
except Exception:  # pragma: no cover - optional import in minimal builds
    CanonicalEventAvroSchema = None  # type: ignore


def _client() -> Optional[SchemaRegistryClient]:  # type: ignore
    url = getattr(settings, "KAFKA_SCHEMA_REGISTRY_URL", "") or os.getenv("KAFKA_SCHEMA_REGISTRY_URL", "")
    if not url or not _HAS_SR:
        return None
    try:
        return SchemaRegistryClient({"url": url})  # type: ignore
    except Exception:
        return None


def try_register_avro_schema(topic: str, schema_dict: dict) -> bool:
    c = _client()
    if c is None or AvroSchema is None:  # type: ignore
        return False
    try:
        subject = f"{topic}-value"
        schema_str = json.dumps(schema_dict)
        avro_schema = AvroSchema(schema_str)  # type: ignore
        c.register_schema(subject, avro_schema)  # type: ignore
        return True
    except Exception:
        return False
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class SchemaRegistryManager:
    def __init__(self):
        self.client = _client()
        self.registered_schemas = {}
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type(Exception)
    )
    async def register_schema_with_retry(self, subject: str, schema_dict: dict, schema_type: str = "AVRO") -> Optional[int]:
        """Register schema with exponential backoff retry"""
        if self.client is None:
            return None
        
        try:
            if schema_type.upper() == "AVRO":
                schema_str = json.dumps(schema_dict)
                avro_schema = AvroSchema(schema_str)
                result = self.client.register_schema(subject, avro_schema)
                logger.info(f"Registered schema for subject {subject}: version {result.version_id}")
                return result.version_id
            else:
                logger.warning(f"Unsupported schema type: {schema_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to register schema for {subject}: {e}")
            raise
    
    async def ensure_subject_version(self, subject: str, schema_dict: dict) -> Optional[int]:
        """Ensure subject has the schema, register if not exists"""
        if self.client is None:
            return None
        
        try:
            # Check if subject exists
            versions = self.client.get_versions(subject)
            if versions:
                # Get latest schema and compare
                latest = self.client.get_schema(subject, versions[-1])
                latest_dict = json.loads(latest.schema_str)
                if latest_dict == schema_dict:
                    return versions[-1]
            
            # Register new version
            return await self.register_schema_with_retry(subject, schema_dict)
        except Exception as e:
            logger.warning(f"Subject check failed for {subject}: {e}")
            # Try to register anyway
            try:
                return await self.register_schema_with_retry(subject, schema_dict)
            except Exception:
                return None
    
    async def bootstrap_schemas(self, schemas: dict[str, dict]):
        """Bootstrap multiple schemas on startup"""
        if self.client is None:
            logger.warning("Schema Registry not available, skipping bootstrap")
            return
        
        for topic, schema_dict in schemas.items():
            subject = f"{topic}-value"
            try:
                version = await self.ensure_subject_version(subject, schema_dict)
                if version:
                    self.registered_schemas[subject] = version
                    logger.info(f"Bootstrapped schema for {subject} v{version}")
                else:
                    logger.error(f"Failed to bootstrap schema for {subject}")
            except Exception as e:
                logger.error(f"Bootstrap failed for {subject}: {e}")

    async def bootstrap_default_schemas(self) -> None:
        schemas = default_topic_schemas()
        if not schemas:
            logger.info("No default schemas defined for bootstrap")
            return
        await self.bootstrap_schemas(schemas)

# Singleton
schema_registry_manager = SchemaRegistryManager()


def default_topic_schemas() -> Dict[str, Dict[str, Any]]:
    """Return the canonical set of topic → schema mappings used during bootstrap."""
    topics: Dict[str, Dict[str, Any]] = {}
    if CanonicalEventAvroSchema is not None:
        try:
            topics["trace.events"] = CanonicalEventAvroSchema.SCHEMA  # type: ignore[attr-defined]
        except Exception:
            logger.warning("Failed to load canonical event schema for bootstrap")
    return topics
