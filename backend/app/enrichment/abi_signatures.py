"""
Common EVM 4-byte selector → function name fallback map and resolver.
This is a lightweight helper used when ABI decoding fails, to provide
human-readable method names for common router/bridge/token functions.
"""
from __future__ import annotations
from typing import Optional

# Minimal curated map. Extend via settings or at runtime if needed.
# Source: Common UniswapV2/V3 Router, ERC20, Bridge methods (heuristics)
SELECTOR_TO_NAME: dict[str, str] = {
    # ERC20
    "0xa9059cbb": "transfer(address,uint256)",
    "0x095ea7b3": "approve(address,uint256)",
    "0x23b872dd": "transferFrom(address,address,uint256)",
    "0x70a08231": "balanceOf(address)",
    "0x313ce567": "decimals()",
    "0x06fdde03": "name()",
    "0x95d89b41": "symbol()",
    # UniswapV2 Router
    "0x38ed1739": "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
    "0x18cbafe5": "swapExactETHForTokens(uint256,address[],address,uint256)",
    "0x8803dbee": "swapExactTokensForETH(uint256,uint256,address[],address,uint256)",
    "0x7ff36ab5": "swapExactETHForTokensSupportingFeeOnTransferTokens(uint256,address[],address,uint256)",
    "0x5c11d795": "swapExactTokensForETHSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)",
    # UniswapV3-like
    "0x414bf389": "exactInputSingle((address,address,uint24,address,uint256,uint256,uint256,uint160))",
    "0xb858183f": "exactInput(bytes)",
    # Bridges (heuristic placeholders)
    "0x12345678": "bridgeTransfer()",
    "0xabcdef12": "bridgeLock()",
}


def resolve_selector_name(selector: Optional[str]) -> Optional[str]:
    """Resolve 4-byte selector to a human-readable function signature.

    Args:
        selector: Hex string starting with 0x and at least 10 chars (0x + 8 hex)

    Returns:
        Function signature string if known, else None
    """
    if not selector or not isinstance(selector, str):
        return None
    s = selector.lower()
    if not s.startswith("0x"):
        return None
    key = s[:10]
    return SELECTOR_TO_NAME.get(key)
