"""Chain-specific address validators and normalizers"""
from __future__ import annotations

import re
from typing import Optional

# Basic regexes for quick validation. Can be extended per-chain.
_ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
_BTC_ADDRESS_RE = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^(bc1)[a-z0-9]{25,62}$")
_SOL_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def is_valid_address(chain: str, address: str) -> bool:
    """Return True if address looks valid for given chain.
    This is a lightweight check; for production, replace with proper libs
    (e.g., eth_utils, bitcoinlib, solders, etc.).
    """
    c = (chain or "").lower().strip()
    a = (address or "").strip()
    if c == "ethereum":
        return bool(_ETH_ADDRESS_RE.match(a))
    if c == "bitcoin":
        return bool(_BTC_ADDRESS_RE.match(a))
    if c == "solana":
        return bool(_SOL_ADDRESS_RE.match(a))
    # Default: unknown chains -> false
    return False


def normalize_address(chain: str, address: str) -> Optional[str]:
    """Normalize an address for the given chain (case, prefix handling).
    Returns None if invalid.
    """
    if not is_valid_address(chain, address):
        return None
    a = address.strip()
    c = chain.lower()
    if c == "ethereum":
        # For now, lower-case. Can replace with EIP-55 checksum later.
        return a.lower()
    if c in {"bitcoin", "solana"}:
        return a
    return a
