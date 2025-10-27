"""Tracing Data Models"""

from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum


class TaintModel(str, Enum):
    """Taint propagation models"""
    FIFO = "fifo"  # First-In-First-Out
    PROPORTIONAL = "proportional"  # Proportional to balances
    HAIRCUT = "haircut"  # Fixed percentage reduction per hop


class TraceDirection(str, Enum):
    """Trace direction"""
    FORWARD = "forward"  # Follow outflows
    BACKWARD = "backward"  # Trace origins
    BOTH = "both"  # Bidirectional


class TaintedTransaction(BaseModel):
    """Transaction with taint information"""
    tx_hash: str
    from_address: str
    to_address: str
    value: Decimal
    timestamp: str
    taint_amount: Decimal = Field(..., description="Amount of tainted value")
    taint_score: float = Field(..., description="Taint score (0-1)")
    hop_distance: int = Field(..., description="Distance from source")
    path: List[str] = Field(default_factory=list, description="Address path")


class TraceNode(BaseModel):
    """Node in trace graph"""
    address: str
    balance: Decimal = Decimal(0)
    total_inflow: Decimal = Decimal(0)
    total_outflow: Decimal = Decimal(0)
    taint_received: Decimal = Decimal(0)
    taint_sent: Decimal = Decimal(0)
    hop_distance: int = 0
    labels: List[str] = Field(default_factory=list)
    risk_score: float = 0.0


class TraceEdge(BaseModel):
    """Edge in trace graph"""
    from_address: str
    to_address: str
    tx_hash: str
    value: Decimal
    taint_value: Decimal
    timestamp: str
    hop: int
    # Optional metadata for cross-chain/bridge detection
    event_type: str | None = None  # e.g., "bridge", "transfer", ...
    bridge: str | None = None      # bridge name/id if known
    chain_from: str | None = None  # source chain id/name
    chain_to: str | None = None    # destination chain id/name


class TraceResult(BaseModel):
    """Complete trace result"""
    trace_id: str
    source_address: str
    direction: TraceDirection
    taint_model: TaintModel
    max_depth: int
    min_taint_threshold: float
    
    # Results
    nodes: Dict[str, TraceNode] = Field(default_factory=dict)
    edges: List[TraceEdge] = Field(default_factory=list)
    tainted_transactions: List[TaintedTransaction] = Field(default_factory=list)
    
    # Statistics
    total_nodes: int = 0
    total_edges: int = 0
    max_hop_reached: int = 0
    total_taint_traced: Decimal = Decimal(0)
    
    # High-risk findings
    high_risk_addresses: List[str] = Field(default_factory=list)
    sanctioned_addresses: List[str] = Field(default_factory=list)
    
    # Metadata
    execution_time_seconds: float = 0.0
    completed: bool = False
    error: Optional[str] = None


class TraceRequest(BaseModel):
    """Request to trace transactions"""
    source_address: str
    direction: TraceDirection = TraceDirection.FORWARD
    taint_model: TaintModel = TaintModel.PROPORTIONAL
    max_depth: int = Field(default=5, ge=1, le=10)
    min_taint_threshold: float = Field(default=0.01, ge=0, le=1)
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    max_nodes: int = Field(default=1000, ge=1, le=10000)

    # Channel toggles
    enable_native: bool = Field(default=True, description="Enable native (coin) flows")
    enable_token: bool = Field(default=True, description="Enable token (ERC20/721/1155) flows")
    enable_bridge: bool = Field(default=True, description="Enable cross-chain bridge expansion")
    enable_utxo: bool = Field(default=True, description="Enable UTXO flows")

    # Channel decays (0-1)
    native_decay: float = Field(default=1.0, ge=0.0, le=1.0)
    token_decay: float = Field(default=1.0, ge=0.0, le=1.0)
    bridge_decay: float = Field(default=0.9, ge=0.0, le=1.0)
    utxo_decay: float = Field(default=1.0, ge=0.0, le=1.0)

    # Robustness & Progress
    io_timeout_seconds: float = Field(default=5.0, ge=0.1, le=60.0, description="Timeout for single I/O calls")
    max_execution_seconds: int = Field(default=25, ge=1, le=300, description="Wall-clock timeout for entire trace")
    progress_emit_interval_ms: int = Field(default=500, ge=50, le=10000, description="Throttle for progress emits")
