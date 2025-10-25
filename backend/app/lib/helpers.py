"""
Helper utilities for Blockchain Forensics Platform
"""

from typing import Optional
from datetime import datetime, timezone
import hashlib
import re


def validate_ethereum_address(address: str) -> bool:
    """
    Validate Ethereum address format
    
    Args:
        address: Ethereum address to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not address:
        return False
    
    # Check format: 0x followed by 40 hex characters
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def validate_tx_hash(tx_hash: str) -> bool:
    """
    Validate transaction hash format
    
    Args:
        tx_hash: Transaction hash to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not tx_hash:
        return False
    
    # Check format: 0x followed by 64 hex characters
    pattern = r'^0x[a-fA-F0-9]{64}$'
    return bool(re.match(pattern, tx_hash))


def generate_trace_id(source_address: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate unique trace ID
    
    Args:
        source_address: Source address for trace
        timestamp: Optional timestamp (default: now)
    
    Returns:
        Unique trace ID (hash)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    data = f"{source_address}_{timestamp.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def format_wei_to_ether(wei: int) -> float:
    """
    Convert Wei to Ether
    
    Args:
        wei: Amount in Wei
    
    Returns:
        Amount in Ether
    """
    return wei / 1e18


def format_ether_to_wei(ether: float) -> int:
    """
    Convert Ether to Wei
    
    Args:
        ether: Amount in Ether
    
    Returns:
        Amount in Wei
    """
    return int(ether * 1e18)


def truncate_address(address: str, length: int = 6) -> str:
    """
    Truncate address for display (0x1234...5678)
    
    Args:
        address: Full address
        length: Number of chars to show on each side
    
    Returns:
        Truncated address
    """
    if not address or len(address) <= length * 2 + 2:
        return address
    
    return f"{address[:length+2]}...{address[-length:]}"


def calculate_risk_level(risk_score: float) -> str:
    """
    Convert risk score to level
    
    Args:
        risk_score: Numeric risk score (0-1)
    
    Returns:
        Risk level string
    """
    if risk_score >= 0.9:
        return "critical"
    elif risk_score >= 0.6:
        return "high"
    elif risk_score >= 0.3:
        return "medium"
    else:
        return "low"


def is_contract_address(address: str, code: Optional[str] = None) -> bool:
    """
    Check if address is a smart contract
    
    Args:
        address: Ethereum address
        code: Optional contract code (if available)
    
    Returns:
        True if contract, False otherwise
    """
    # If code is provided, check if it's not empty
    if code is not None:
        return code != "0x" and len(code) > 2
    
    # Otherwise, would need to query blockchain (placeholder)
    return False


def generate_idempotency_key(
    source_address: str,
    direction: str,
    max_depth: int
) -> str:
    """
    Generate idempotency key for trace requests
    
    Args:
        source_address: Source address
        direction: Trace direction
        max_depth: Max depth
    
    Returns:
        Idempotency key
    """
    data = f"{source_address}_{direction}_{max_depth}"
    return hashlib.sha256(data.encode()).hexdigest()
