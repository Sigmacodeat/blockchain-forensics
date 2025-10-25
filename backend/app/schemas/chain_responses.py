"""
Pydantic response models for chain utils endpoints
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SolanaBlockResponse(BaseModel):
    slot: int
    result: Optional[Dict[str, Any]]


class SolanaTxResponse(BaseModel):
    signature: str
    result: Optional[Dict[str, Any]]


class CanonicalEventModel(BaseModel):
    event_id: str
    chain: str
    block_number: int
    timestamp: Any
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    value: Optional[Any] = None
    tx_hash: Optional[str] = None
    event_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SolanaCanonicalResponse(BaseModel):
    signature: str
    canonical: Optional[CanonicalEventModel] | Dict[str, Any] | None = None
    error: Optional[str] = None


class BitcoinBlockResponse(BaseModel):
    height: int
    hash: Optional[str] = None
    time: Optional[int] = None
    tx_count: int
    status: str


class BitcoinTxResponse(BaseModel):
    txid: str
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class BitcoinTxNormalizedVin(BaseModel):
    txid: Optional[str] = None
    vout: Optional[int] = None
    coinbase: Optional[str] = None
    sequence: Optional[int] = None


class BitcoinTxNormalizedVout(BaseModel):
    n: int
    value: float
    addresses: List[str] = Field(default_factory=list)
    type: Optional[str] = None


class BitcoinTxNormalized(BaseModel):
    txid: str
    size: Optional[int] = None
    version: Optional[int] = None
    locktime: Optional[int] = None
    vin: List[BitcoinTxNormalizedVin]
    vout: List[BitcoinTxNormalizedVout]


class BitcoinEdgeEndpoint(BaseModel):
    txid: str
    vout: int


class BitcoinEdge(BaseModel):
    from_: BitcoinEdgeEndpoint = Field(alias="from")
    to: BitcoinEdgeEndpoint
    value: float

    model_config = ConfigDict(populate_by_name=True)


class BitcoinEdgesResponse(BaseModel):
    txid: str
    edges: List[BitcoinEdge]
    fee: Optional[float] = None
    method: Optional[str] = None


class EthereumTxResponse(BaseModel):
    hash: str
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class EthereumCanonicalResponse(BaseModel):
    hash: str
    canonical: Optional[CanonicalEventModel] | Dict[str, Any] | None = None
    status: Optional[str] = None
