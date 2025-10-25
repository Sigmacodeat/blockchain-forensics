"""Chain Adapters package with lazy imports.

Avoid importing heavy/optional dependencies (e.g. web3) at import time.
Instead, resolve adapters on first attribute access.
"""

from typing import TYPE_CHECKING
import importlib

__all__ = [
    "IChainAdapter",
    "EthereumAdapter",
    "PolygonAdapter",
    "ArbitrumAdapter",
    "OptimismAdapter",
    "BaseAdapter",
    "FantomAdapter",
    "CeloAdapter",
    "MoonbeamAdapter",
    "AuroraAdapter",
    "StarknetAdapter",
    "CardanoAdapter",
    "NearAdapter",
    "SuiAdapter",
    "AptosAdapter",
    "BscAdapter",
    "GnosisAdapter",
    "ZkSyncAdapter",
    "ScrollAdapter",
    "LineaAdapter",
    "TronAdapter",
    "get_adapter",
]

_LAZY_ATTRS = {
    "IChainAdapter": ("app.adapters.base", "IChainAdapter"),
    "BaseAdapter": ("app.adapters.base_adapter", "BaseAdapter"),
    "EthereumAdapter": ("app.adapters.ethereum_adapter", "EthereumAdapter"),
    "PolygonAdapter": ("app.adapters.polygon_adapter", "PolygonAdapter"),
    "ArbitrumAdapter": ("app.adapters.arbitrum_adapter", "ArbitrumAdapter"),
    "OptimismAdapter": ("app.adapters.optimism_adapter", "OptimismAdapter"),
    "FantomAdapter": ("app.adapters.fantom_adapter", "FantomAdapter"),
    "CeloAdapter": ("app.adapters.celo_adapter", "CeloAdapter"),
    "MoonbeamAdapter": ("app.adapters.moonbeam_adapter", "MoonbeamAdapter"),
    "AuroraAdapter": ("app.adapters.aurora_adapter", "AuroraAdapter"),
    "StarknetAdapter": ("app.adapters.starknet_adapter", "StarknetAdapter"),
    "CardanoAdapter": ("app.adapters.cardano_adapter", "CardanoAdapter"),
    "NearAdapter": ("app.adapters.near_adapter", "NearAdapter"),
    "SuiAdapter": ("app.adapters.sui_adapter", "SuiAdapter"),
    "AptosAdapter": ("app.adapters.aptos_adapter", "AptosAdapter"),
    "BscAdapter": ("app.adapters.bsc_adapter", "BscAdapter"),
    "GnosisAdapter": ("app.adapters.gnosis_adapter", "GnosisAdapter"),
    "ZkSyncAdapter": ("app.adapters.zksync_adapter", "ZkSyncAdapter"),
    "ScrollAdapter": ("app.adapters.scroll_adapter", "ScrollAdapter"),
    "LineaAdapter": ("app.adapters.linea_adapter", "LineaAdapter"),
    "TronAdapter": ("app.adapters.tron_adapter", "TronAdapter"),
}

def __getattr__(name: str):
    target = _LAZY_ATTRS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr_name = target
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)
    except Exception as e:  # pragma: no cover - keep import-time robust in tests
        raise ImportError(f"Failed to import {attr_name} from {module_name}: {e}") from e

def get_adapter(chain: str):
    """Return a chain adapter instance for the given chain id.

    Delegates to the multi-chain engine's adapter factory to avoid
    duplicating registry logic.
    """
    try:
        from app.services.multi_chain import multi_chain_engine  # lazy import
        return multi_chain_engine.adapter_factory.get_adapter(chain)
    except Exception as e:  # pragma: no cover
        raise ImportError(f"Could not resolve adapter for chain '{chain}': {e}") from e

# Help static type checkers without importing at runtime
if TYPE_CHECKING:  # pragma: no cover
    from app.adapters.base import IChainAdapter  # noqa: F401
    from app.adapters.base_adapter import BaseAdapter  # noqa: F401
    from app.adapters.ethereum_adapter import EthereumAdapter  # noqa: F401
    from app.adapters.polygon_adapter import PolygonAdapter  # noqa: F401
    from app.adapters.arbitrum_adapter import ArbitrumAdapter  # noqa: F401
    from app.adapters.optimism_adapter import OptimismAdapter  # noqa: F401
