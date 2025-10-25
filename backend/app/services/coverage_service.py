"""
Coverage Service
Aggregates dynamic adapter health and static heuristics for coverage API
"""
from typing import Dict, Any

from app.config import settings
from app.services.multi_chain import multi_chain_engine


async def get_adapter_health() -> Dict[str, Dict[str, Any]]:
    """Collect lightweight health info from available adapters."""
    # Ethereum: treat as ready if RPC URL configured
    eth_rpc = getattr(settings, "ETHEREUM_RPC_URL", None)
    eth_health = {
        "module": "adapters.ethereum_adapter",
        "status": "ready" if eth_rpc else "unknown",
        "rpc": bool(eth_rpc),
    }

    # Solana: stubbed health
    sol_rpc = getattr(settings, "SOLANA_RPC_URL", None) or "https://api.mainnet-beta.solana.com"
    try:
        from app.adapters.solana_adapter import create_solana_adapter  # type: ignore

        sol = create_solana_adapter(sol_rpc)
        sol_health = await sol.health()
        sol_health.update({"module": "adapters.solana_adapter"})
    except Exception:  # ImportError or runtime init issues
        sol_health = {
            "module": "adapters.solana_adapter",
            "status": "stub",
            "rpc": bool(sol_rpc),
        }

    # Bitcoin: stubbed health
    btc_rpc = getattr(settings, "BITCOIN_RPC_URL", None)
    try:
        from app.adapters.bitcoin_adapter import BitcoinAdapter  # type: ignore

        btc = BitcoinAdapter(btc_rpc)
        btc_health = await btc.health()
        btc_health.update({"module": "adapters.bitcoin_adapter"})
    except Exception:  # ImportError or runtime init issues
        btc_health = {
            "module": "adapters.bitcoin_adapter",
            "status": "stub",
            "rpc": bool(btc_rpc),
        }

    return {
        "ethereum": eth_health,
        "solana": sol_health,
        "bitcoin": btc_health,
    }


async def aggregate_coverage() -> Dict[str, Any]:
    """Return full coverage document combining adapters and heuristics."""
    adapters = await get_adapter_health()

    # Lazy import heuristics with safe fallbacks in tests/missing deps
    try:
        from app.normalizer.bridge_patterns import list_bridge_patterns  # type: ignore
        bridges = list_bridge_patterns()
    except Exception:
        bridges = []

    try:
        from app.tracing.mixer_rules import list_mixer_rules  # type: ignore
        mixers = list_mixer_rules()
    except Exception:
        mixers = []

    # Build chains dynamically from the registry
    supported = multi_chain_engine.adapter_factory.get_supported_chains()
    chains = []
    for ci in supported:
        chain_id = ci.chain_id
        health = adapters.get(chain_id, {})
        status = health.get("status", "unknown")
        if not status and health.get("rpc"):
            status = "beta"
        chains.append({
            "name": chain_id,
            "type": ci.chain_type.name,
            "status": status or "unknown",
            "features": ci.features or [],
            "native_asset": ci.symbol,
            "explorer": ci.block_explorer_url or "",
        })

    # Normalize bridges/mixers for UI
    bridges_norm = [
        {
            "name": b.get("name"),
            "chains": b.get("chains", []),
            "status": b.get("status", "planned"),
        }
        for b in bridges
    ]
    mixers_norm = [
        {
            "name": m.get("name"),
            "chains": [m.get("chain")] if m.get("chain") else m.get("chains", []),
            "status": m.get("status", "planned"),
        }
        for m in mixers
    ]

    # Adapters minimal projection
    adapters_proj = {
        k: {"module": v.get("module", ""), "status": v.get("status", "unknown")} for k, v in adapters.items()
    }

    return {
        "chains": chains,
        "bridges": bridges_norm,
        "mixers": mixers_norm,
        "dexes": [
            {"name": "Uniswap", "chains": ["ethereum"], "status": "paths"},
            {"name": "SushiSwap", "chains": ["ethereum"], "status": "planned"},
        ],
        "adapters": adapters_proj,
        "version": "0.1.2",
    }
