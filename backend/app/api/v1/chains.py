"""
Chains API - Supported Blockchain Networks
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/supported")
async def get_supported_chains() -> Dict[str, Any]:
    """
    Returns list of all supported blockchain networks
    
    Returns:
        chains: List of supported chains with metadata
        total: Total number of supported chains
    """
    
    chains = [
        # EVM Chains
        {
            "id": "ethereum",
            "name": "Ethereum",
            "type": "evm",
            "native_token": "ETH",
            "explorer": "https://etherscan.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "polygon",
            "name": "Polygon",
            "type": "evm",
            "native_token": "MATIC",
            "explorer": "https://polygonscan.com",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "arbitrum",
            "name": "Arbitrum One",
            "type": "evm_l2",
            "native_token": "ETH",
            "explorer": "https://arbiscan.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "optimism",
            "name": "Optimism",
            "type": "evm_l2",
            "native_token": "ETH",
            "explorer": "https://optimistic.etherscan.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "base",
            "name": "Base",
            "type": "evm_l2",
            "native_token": "ETH",
            "explorer": "https://basescan.org",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "bsc",
            "name": "BNB Smart Chain",
            "type": "evm",
            "native_token": "BNB",
            "explorer": "https://bscscan.com",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "avalanche",
            "name": "Avalanche C-Chain",
            "type": "evm",
            "native_token": "AVAX",
            "explorer": "https://snowtrace.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "gnosis",
            "name": "Gnosis Chain (xDai)",
            "type": "evm",
            "native_token": "xDAI",
            "explorer": "https://gnosisscan.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "celo",
            "name": "Celo",
            "type": "evm",
            "native_token": "CELO",
            "explorer": "https://celoscan.io",
            "testnet": False,
            "status": "active"
        },
        
        # UTXO Chains
        {
            "id": "bitcoin",
            "name": "Bitcoin",
            "type": "utxo",
            "native_token": "BTC",
            "explorer": "https://blockchair.com/bitcoin",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "litecoin",
            "name": "Litecoin",
            "type": "utxo",
            "native_token": "LTC",
            "explorer": "https://blockchair.com/litecoin",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "dogecoin",
            "name": "Dogecoin",
            "type": "utxo",
            "native_token": "DOGE",
            "explorer": "https://blockchair.com/dogecoin",
            "testnet": False,
            "status": "active"
        },
        
        # Other Chains
        {
            "id": "solana",
            "name": "Solana",
            "type": "svm",
            "native_token": "SOL",
            "explorer": "https://solscan.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "tron",
            "name": "Tron",
            "type": "tvm",
            "native_token": "TRX",
            "explorer": "https://tronscan.org",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "cardano",
            "name": "Cardano",
            "type": "utxo",
            "native_token": "ADA",
            "explorer": "https://cardanoscan.io",
            "testnet": False,
            "status": "beta"
        },
        {
            "id": "ripple",
            "name": "Ripple (XRP Ledger)",
            "type": "xrpl",
            "native_token": "XRP",
            "explorer": "https://xrpscan.com",
            "testnet": False,
            "status": "beta"
        },
        
        # L2s
        {
            "id": "zksync",
            "name": "zkSync Era",
            "type": "evm_l2",
            "native_token": "ETH",
            "explorer": "https://explorer.zksync.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "linea",
            "name": "Linea",
            "type": "evm_l2",
            "native_token": "ETH",
            "explorer": "https://lineascan.build",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "scroll",
            "name": "Scroll",
            "type": "evm_l2",
            "native_token": "ETH",
            "explorer": "https://scrollscan.com",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "mantle",
            "name": "Mantle",
            "type": "evm_l2",
            "native_token": "MNT",
            "explorer": "https://explorer.mantle.xyz",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "blast",
            "name": "Blast",
            "type": "evm_l2",
            "native_token": "ETH",
            "explorer": "https://blastscan.io",
            "testnet": False,
            "status": "active"
        },
        {
            "id": "starknet",
            "name": "Starknet",
            "type": "cairo",
            "native_token": "ETH",
            "explorer": "https://starkscan.co",
            "testnet": False,
            "status": "beta"
        }
    ]
    
    # Group by type
    by_type = {}
    for chain in chains:
        chain_type = chain["type"]
        if chain_type not in by_type:
            by_type[chain_type] = []
        by_type[chain_type].append(chain["name"])
    
    return {
        "chains": chains,
        "total": len(chains),
        "by_type": by_type,
        "active_count": len([c for c in chains if c["status"] == "active"]),
        "beta_count": len([c for c in chains if c["status"] == "beta"])
    }


@router.get("/capabilities")
async def get_chain_capabilities() -> Dict[str, Any]:
    """
    Returns platform capabilities for blockchain forensics
    """
    
    return {
        "tracing": {
            "supported_chains": ["ethereum", "polygon", "arbitrum", "optimism", "base", "bsc", "avalanche"],
            "max_depth": 10,
            "max_nodes": 10000,
            "taint_models": ["fifo", "proportional", "haircut"],
            "supports_token_flows": True,
            "supports_bridge_tracking": True
        },
        "address_validation": {
            "ethereum": ["0x-prefixed", "42-chars"],
            "bitcoin": ["bech32", "p2pkh", "p2sh"],
            "solana": ["base58", "32-44 chars"]
        },
        "entity_labels": {
            "total_entities": 8500,
            "categories": ["exchange", "mixer", "defi", "sanctions", "scam", "whale", "dao", "nft"],
            "sanctions_lists": ["OFAC", "UN", "EU", "UK", "CA", "AU", "CH", "JP", "SG"]
        },
        "performance": {
            "api_latency_target_ms": 100,
            "trace_completion_estimate_seconds": "5-60",
            "concurrent_traces": 10
        }
    }
