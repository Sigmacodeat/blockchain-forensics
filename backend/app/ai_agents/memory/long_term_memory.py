"""
Long-Term Memory Manager.
Persistent storage beyond 24h Redis TTL for important findings.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class Memory(BaseModel):
    """Single memory entry"""
    memory_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    content: str
    context: Dict[str, Any]
    importance: float  # 0-1
    created_at: datetime
    expires_at: Optional[datetime] = None
    tags: List[str] = []
    access_count: int = 0


class LongTermMemoryManager:
    """
    Persistent memory management beyond Redis TTL.
    
    Storage strategy:
    - Critical findings (importance > 0.8): Permanent
    - Important findings (0.5-0.8): 30 days
    - Standard findings (<0.5): 7 days
    
    Use cases:
    - Remember important addresses
    - Store investigation patterns
    - Cache user preferences
    - Remember key findings
    """
    
    def __init__(self):
        """Initialize memory manager"""
        self.default_ttl = 86400 * 7  # 7 days
        logger.info("✅ LongTermMemoryManager initialized")
    
    async def store(
        self,
        content: str,
        context: Dict[str, Any],
        importance: float = 0.5,
        ttl: Optional[int] = None,
        tags: List[str] = [],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Store memory in Postgres (persistent).
        
        Args:
            content: Memory content (text)
            context: Additional context (JSON)
            importance: Importance score 0-1
            ttl: Time to live in seconds (None = permanent)
            tags: Tags for categorization
            user_id: User ID (optional)
            session_id: Session ID (optional)
        
        Returns:
            Memory ID
        """
        try:
            from app.db.postgres import postgres_client
            
            # Generate memory ID
            memory_id = self._generate_id(content, datetime.utcnow().isoformat())
            
            # Calculate expiration
            expires_at = None
            if ttl is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            elif importance < 0.5:
                # Low importance: 7 days
                expires_at = datetime.utcnow() + timedelta(days=7)
            elif importance < 0.8:
                # Medium importance: 30 days
                expires_at = datetime.utcnow() + timedelta(days=30)
            # High importance (>0.8): permanent (expires_at = None)
            
            # Store in database
            await postgres_client.execute("""
                INSERT INTO agent_memories 
                (memory_id, user_id, session_id, content, context, importance, created_at, expires_at, tags, access_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (memory_id) 
                DO UPDATE SET
                    content = EXCLUDED.content,
                    context = EXCLUDED.context,
                    importance = EXCLUDED.importance,
                    tags = EXCLUDED.tags,
                    access_count = agent_memories.access_count + 1
            """, memory_id, user_id, session_id, content, json.dumps(context), 
                importance, datetime.utcnow(), expires_at, tags, 0)
            
            logger.info(f"Stored memory: {memory_id} (importance: {importance})")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}", exc_info=True)
            
            # Fallback: return generated ID (memory not persisted)
            return self._generate_id(content, datetime.utcnow().isoformat())
    
    async def recall(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.3,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Memory]:
        """
        Semantic search over memories.
        
        Args:
            query: Search query
            limit: Maximum results
            min_importance: Minimum importance
            user_id: Filter by user
            tags: Filter by tags
        
        Returns:
            List of matching memories
        """
        try:
            from app.db.postgres import postgres_client
            
            # Build query
            sql = """
                SELECT memory_id, user_id, session_id, content, context, importance, 
                       created_at, expires_at, tags, access_count
                FROM agent_memories
                WHERE importance >= $1
                  AND (expires_at IS NULL OR expires_at > NOW())
            """
            params = [min_importance]
            param_count = 1
            
            # User filter
            if user_id:
                param_count += 1
                sql += f" AND user_id = ${param_count}"
                params.append(user_id)
            
            # Tag filter
            if tags:
                param_count += 1
                sql += f" AND tags && ${param_count}"
                params.append(tags)
            
            # Text search (simple ILIKE for now)
            param_count += 1
            sql += f" AND content ILIKE ${param_count}"
            params.append(f"%{query}%")
            
            # Order and limit
            param_count += 1
            sql += f" ORDER BY importance DESC, created_at DESC LIMIT ${param_count}"
            params.append(limit)
            
            results = await postgres_client.fetch(sql, *params)
            
            # Convert to Memory objects
            memories = []
            for row in results:
                memories.append(Memory(
                    memory_id=row["memory_id"],
                    user_id=row["user_id"],
                    session_id=row["session_id"],
                    content=row["content"],
                    context=json.loads(row["context"]) if row["context"] else {},
                    importance=row["importance"],
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    tags=row["tags"] or [],
                    access_count=row["access_count"]
                ))
                
                # Increment access count
                await postgres_client.execute(
                    "UPDATE agent_memories SET access_count = access_count + 1 WHERE memory_id = $1",
                    row["memory_id"]
                )
            
            logger.info(f"Recalled {len(memories)} memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Error recalling memories: {e}", exc_info=True)
            return []
    
    async def forget(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory to delete
        
        Returns:
            True if deleted
        """
        try:
            from app.db.postgres import postgres_client
            
            await postgres_client.execute(
                "DELETE FROM agent_memories WHERE memory_id = $1",
                memory_id
            )
            
            logger.info(f"Forgot memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error forgetting memory: {e}", exc_info=True)
            return False
    
    async def cleanup_expired(self) -> int:
        """
        Clean up expired memories.
        
        Returns:
            Number of memories deleted
        """
        try:
            from app.db.postgres import postgres_client
            
            result = await postgres_client.execute(
                "DELETE FROM agent_memories WHERE expires_at IS NOT NULL AND expires_at <= NOW()"
            )
            
            # Extract count from result (format: "DELETE N")
            count = int(result.split()[-1]) if result else 0
            
            logger.info(f"Cleaned up {count} expired memories")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up memories: {e}", exc_info=True)
            return 0
    
    async def summarize_conversation(
        self,
        messages: List[Dict],
        max_length: int = 200
    ) -> str:
        """
        Summarize conversation history for compression.
        
        Args:
            messages: Chat messages
            max_length: Maximum summary length
        
        Returns:
            Summary text
        """
        try:
            from app.ai_agents.agent import get_agent
            agent = get_agent()
            
            summary_prompt = f"""
            Summarize this conversation into key facts (max {max_length} words):
            
            {json.dumps(messages, indent=2, default=str)[:2000]}
            
            Focus on:
            - Important findings
            - Decisions made
            - Actions taken
            - Key addresses/transactions
            """
            
            result = await agent.llm.ainvoke([
                {"role": "system", "content": "You are a conversation summarizer."},
                {"role": "user", "content": summary_prompt}
            ])
            
            summary = result.content[:max_length * 6]  # ~6 chars per word
            
            # Store as memory
            await self.store(
                content=summary,
                context={"type": "conversation_summary", "message_count": len(messages)},
                importance=0.6,
                ttl=86400 * 7,  # 7 days
                tags=["summary", "conversation"]
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}", exc_info=True)
            return "Summary unavailable"
    
    def _generate_id(self, content: str, timestamp: str) -> str:
        """Generate deterministic memory ID"""
        data = f"{content}{timestamp}"
        return f"mem_{hashlib.sha256(data.encode()).hexdigest()[:16]}"


logger.info("✅ Long-Term Memory Manager loaded")
