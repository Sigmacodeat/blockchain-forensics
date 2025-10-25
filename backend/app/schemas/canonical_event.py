"""Canonical Event Schema - Chain-Agnostic Event Format"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal


class CanonicalEvent(BaseModel):
    """
    Chain-agnostic event format for all blockchain transactions.
    Extended with ML features for risk scoring and clustering.
    """
    
    # Core Transaction Fields
    event_id: str = Field(..., description="Unique event identifier")
    chain: str = Field(..., description="Blockchain name (eth, btc, sol, etc.)")
    block_number: int = Field(..., description="Block number")
    block_timestamp: datetime = Field(..., description="Block timestamp")
    tx_hash: str = Field(..., description="Transaction hash")
    tx_index: int = Field(..., description="Transaction index in block")
    
    # Transaction Details
    from_address: str = Field(..., description="Sender address")
    to_address: Optional[str] = Field(None, description="Recipient address (null for contract creation)")
    value: Decimal = Field(..., description="Value transferred in smallest unit")
    value_usd: Optional[Decimal] = Field(None, description="USD value at transaction time")
    
    # Gas & Fees
    gas_used: Optional[int] = Field(None, description="Gas used")
    gas_price: Optional[int] = Field(None, description="Gas price in wei")
    fee: Optional[Decimal] = Field(None, description="Total fee paid")
    
    # Status
    status: int = Field(..., description="0=failed, 1=success")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Event Type & Classification
    event_type: str = Field(..., description="transfer, swap, bridge, contract_call, etc.")
    contract_address: Optional[str] = Field(None, description="Contract address if applicable")
    method_name: Optional[str] = Field(None, description="Contract method called")
    
    # Token Information
    token_address: Optional[str] = Field(None, description="Token contract address")
    token_symbol: Optional[str] = Field(None, description="Token symbol")
    token_decimals: Optional[int] = Field(None, description="Token decimals")
    
    # ML Features (added by enrichment)
    risk_score: Optional[float] = Field(None, description="ML-based risk score (0-1)")
    cluster_id: Optional[str] = Field(None, description="Wallet cluster ID")
    
    # Cross-Chain Links
    cross_chain_links: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Links to bridge events on other chains"
    )
    
    # Enrichment Data
    labels: List[str] = Field(default_factory=list, description="Address labels")
    tags: List[str] = Field(default_factory=list, description="Transaction tags")
    
    # Metadata
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., description="Data source (rpc, archive, api)")
    
    # Idempotency
    idempotency_key: str = Field(..., description="Unique key for deduplication")
    
    # Additional Data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chain-specific data")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "eth_tx_0x123abc...",
                "chain": "ethereum",
                "block_number": 18500000,
                "block_timestamp": "2024-01-15T10:30:00Z",
                "tx_hash": "0x123abc...",
                "tx_index": 42,
                "from_address": "0xabc123...",
                "to_address": "0xdef456...",
                "value": "1000000000000000000",
                "value_usd": "3500.00",
                "gas_used": 21000,
                "gas_price": 50000000000,
                "fee": "1050000000000000",
                "status": 1,
                "event_type": "transfer",
                "risk_score": 0.15,
                "cluster_id": "cluster_abc123",
                "labels": ["exchange", "binance"],
                "tags": ["large_transfer"],
                "idempotency_key": "eth_18500000_42",
                "source": "rpc",
                "metadata": {}
            }
        }
    )


class CanonicalEventAvroSchema:
    """Avro Schema for Kafka serialization"""
    
    SCHEMA = {
        "type": "record",
        "name": "CanonicalEvent",
        "namespace": "com.forensics.blockchain",
        "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "chain", "type": "string"},
            {"name": "block_number", "type": "long"},
            {"name": "block_timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
            {"name": "tx_hash", "type": "string"},
            {"name": "tx_index", "type": "int"},
            {"name": "from_address", "type": "string"},
            {"name": "to_address", "type": ["null", "string"]},
            {"name": "value", "type": "string"},  # Decimal as string
            {"name": "value_usd", "type": ["null", "string"]},
            {"name": "gas_used", "type": ["null", "long"]},
            {"name": "gas_price", "type": ["null", "long"]},
            {"name": "fee", "type": ["null", "string"]},
            {"name": "status", "type": "int"},
            {"name": "error_message", "type": ["null", "string"]},
            {"name": "event_type", "type": "string"},
            {"name": "contract_address", "type": ["null", "string"]},
            {"name": "method_name", "type": ["null", "string"]},
            {"name": "token_address", "type": ["null", "string"]},
            {"name": "token_symbol", "type": ["null", "string"]},
            {"name": "token_decimals", "type": ["null", "int"]},
            {"name": "risk_score", "type": ["null", "float"]},
            {"name": "cluster_id", "type": ["null", "string"]},
            {
                "name": "cross_chain_links",
                "type": {
                    "type": "array",
                    "items": {
                        "type": "map",
                        "values": "string"
                    }
                }
            },
            {"name": "labels", "type": {"type": "array", "items": "string"}},
            {"name": "tags", "type": {"type": "array", "items": "string"}},
            {"name": "ingested_at", "type": {"type": "long", "logicalType": "timestamp-millis"}},
            {"name": "source", "type": "string"},
            {"name": "idempotency_key", "type": "string"},
            {
                "name": "metadata",
                "type": {
                    "type": "map",
                    "values": "string"
                }
            }
        ]
    }
