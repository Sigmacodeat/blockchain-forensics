"""
Qdrant Vector Database Client
Für Smart Contract Bytecode Similarity, RAG, und ML-Embeddings
"""

import logging
from typing import List, Dict, Optional
import os
try:
    from qdrant_client import QdrantClient as QdrantBase
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue
    )
    _QDRANT_AVAILABLE = True
except Exception:
    QdrantBase = None  # type: ignore
    Distance = VectorParams = PointStruct = Filter = FieldCondition = MatchValue = None  # type: ignore
    _QDRANT_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantClient:
    """Qdrant Client für Vector Operations"""
    
    # Collection names
    CONTRACT_BYTECODE_COLLECTION = "contract_bytecode"
    ADDRESS_EMBEDDINGS_COLLECTION = "address_embeddings"
    REPORT_EMBEDDINGS_COLLECTION = "report_embeddings"
    
    def __init__(self):
        self.client = None
        # In Testmodus keine Netzwerk-Initialisierung erzwingen
        if os.getenv("TEST_MODE") == "1" or not _QDRANT_AVAILABLE:
            logger.warning("Qdrant client disabled (TEST_MODE=1)")
            return
        try:
            self.client = QdrantBase(url=settings.QDRANT_URL)
            self._ensure_collections()
            logger.info("Qdrant client initialized")
        except Exception as e:
            # Nicht hart fehlschlagen – erlaubt App-Start ohne laufenden Qdrant
            logger.warning(f"Qdrant init skipped due to error: {e}")
    
    def _ensure_collections(self):
        """Create collections if they don't exist"""
        collections = [
            {
                "name": self.CONTRACT_BYTECODE_COLLECTION,
                "vector_size": 1536,  # OpenAI text-embedding-3-large
                "distance": Distance.COSINE
            },
            {
                "name": self.ADDRESS_EMBEDDINGS_COLLECTION,
                "vector_size": 1536,
                "distance": Distance.COSINE
            },
            {
                "name": self.REPORT_EMBEDDINGS_COLLECTION,
                "vector_size": 1536,
                "distance": Distance.COSINE
            }
        ]
        
        if self.client is None:
            return
        existing = [col.name for col in self.client.get_collections().collections]
        
        for collection in collections:
            if collection["name"] not in existing:
                self.client.create_collection(
                    collection_name=collection["name"],
                    vectors_config=VectorParams(
                        size=collection["vector_size"],
                        distance=collection["distance"]
                    )
                )
                logger.info(f"Created Qdrant collection: {collection['name']}")
    
    async def store_contract_bytecode(
        self,
        contract_address: str,
        bytecode: str,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ):
        """
        Store contract bytecode embedding for similarity search
        
        **Use Case:**
        - AnChain.AI: Smart Contract Bytecode Similarity
        - Detect similar scam contracts
        - Clone detection
        """
        if self.client is None:
            return
        point = PointStruct(
            id=hash(contract_address) & 0x7FFFFFFFFFFFFFFF,  # Positive int
            vector=embedding,
            payload={
                "contract_address": contract_address.lower(),
                "bytecode_hash": hash(bytecode),
                "metadata": metadata or {}
            }
        )
        
        self.client.upsert(
            collection_name=self.CONTRACT_BYTECODE_COLLECTION,
            points=[point]
        )
        
        logger.debug(f"Stored bytecode embedding for {contract_address}")
    
    async def find_similar_contracts(
        self,
        embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.8
    ) -> List[Dict]:
        """
        Find similar contracts by bytecode embedding
        
        Returns:
            List of similar contracts with scores
        """
        if self.client is None:
            return []
        results = self.client.search(
            collection_name=self.CONTRACT_BYTECODE_COLLECTION,
            query_vector=embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        similar = []
        for result in results:
            similar.append({
                "contract_address": result.payload.get("contract_address"),
                "similarity_score": result.score,
                "metadata": result.payload.get("metadata", {})
            })
        
        return similar
    
    async def store_address_embedding(
        self,
        address: str,
        embedding: List[float],
        features: Dict
    ):
        """
        Store address behavioral embedding
        
        **Features:**
        - Transaction patterns
        - Network behavior
        - Temporal activity
        - Entity classification
        """
        point = PointStruct(
            id=hash(address) & 0x7FFFFFFFFFFFFFFF,
            vector=embedding,
            payload={
                "address": address.lower(),
                "features": features
            }
        )
        
        self.client.upsert(
            collection_name=self.ADDRESS_EMBEDDINGS_COLLECTION,
            points=[point]
        )
    
    async def find_similar_addresses(
        self,
        embedding: List[float],
        limit: int = 20,
        score_threshold: float = 0.85
    ) -> List[Dict]:
        """
        Find addresses with similar behavioral patterns
        
        **Use Cases:**
        - Wallet clustering (Chainalysis: 100+ heuristics)
        - Sybil detection
        - Entity resolution
        """
        results = self.client.search(
            collection_name=self.ADDRESS_EMBEDDINGS_COLLECTION,
            query_vector=embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        similar = []
        for result in results:
            similar.append({
                "address": result.payload.get("address"),
                "similarity_score": result.score,
                "features": result.payload.get("features", {})
            })
        
        return similar
    
    async def store_report(
        self,
        report_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict
    ):
        """
        Store forensic report for RAG (Retrieval-Augmented Generation)
        
        **Use Cases:**
        - Similar case lookup
        - Precedent search
        - Knowledge base
        """
        point = PointStruct(
            id=hash(report_id) & 0x7FFFFFFFFFFFFFFF,
            vector=embedding,
            payload={
                "report_id": report_id,
                "content_preview": content[:500],
                "metadata": metadata
            }
        )
        
        self.client.upsert(
            collection_name=self.REPORT_EMBEDDINGS_COLLECTION,
            points=[point]
        )
    
    async def search_similar_reports(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for similar forensic reports (RAG)
        
        Returns:
            Similar reports for context
        """
        results = self.client.search(
            collection_name=self.REPORT_EMBEDDINGS_COLLECTION,
            query_vector=query_embedding,
            limit=limit
        )
        
        reports = []
        for result in results:
            reports.append({
                "report_id": result.payload.get("report_id"),
                "relevance_score": result.score,
                "preview": result.payload.get("content_preview"),
                "metadata": result.payload.get("metadata", {})
            })
        
        return reports
    
    def verify_connectivity(self) -> bool:
        """Verify Qdrant connection"""
        if self.client is None:
            return False
        try:
            collections = self.client.get_collections()
            return len(collections.collections) > 0
        except Exception as e:
            logger.error(f"Qdrant connectivity check failed: {e}")
            return False
    
    def close(self):
        """Close Qdrant connection"""
        if self.client is not None:
            self.client.close()
            logger.info("Qdrant connection closed")


# Singleton instance with safe fallback
try:
    qdrant_client = QdrantClient()
except Exception:
    os.environ["TEST_MODE"] = "1"
    qdrant_client = QdrantClient()
