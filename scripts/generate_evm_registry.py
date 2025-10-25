"""
EVM Registry Generator
Fetches EVM chains from chainid.network and generates registry entries
"""
import json
import asyncio
from typing import List, Dict, Any
import httpx

from app.services.multi_chain import ChainInfo, ChainType


async def fetch_chainlist_data() -> List[Dict[str, Any]]:
    """Fetch EVM chain list from chainid.network"""
    url = "https://chainid.network/chains.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        return response.json()


def generate_registry_entries(chains: List[Dict[str, Any]]) -> str:
    """Generate Python registry code for given chains"""
    entries = []

    for chain in chains:
        chain_id_num = chain.get("chainId")
        chain_key = str(chain.get("name", "")).strip() or str(chain_id_num)
        name = chain.get("title") or chain.get("name") or str(chain_id_num)
        native_currency = chain.get("nativeCurrency", {})
        symbol = native_currency.get("symbol", "ETH")
        decimals = native_currency.get("decimals", 18)
        rpcs = chain.get("rpc", [])
        explorers = chain.get("explorers", [])
        explorer_url = explorers[0].get("url", "") if explorers else ""

        # Skip obvious testnets
        lower_name = (name or "").lower()
        if any(k in lower_name for k in ["testnet", "goerli", "sepolia", "holesky", "chiado", "mumbai", "rinkeby", "kovan"]):
            continue

        # Map to our ChainInfo format
        env_key = chain_key.upper().replace(" ", "_").replace("-", "_")
        rpc_list = [rpc for rpc in rpcs if isinstance(rpc, str)]
        entry = (
            f'            "{chain_key}": ChainInfo(\n'
            f'                chain_id="{chain_key}",\n'
            f'                name="{name}",\n'
            f'                symbol="{symbol}",\n'
            f'                chain_type=ChainType.EVM,\n'
            f'                rpc_urls=[url for url in [_cfg("{env_key}_RPC_URL", None)] + {rpc_list} if url],\n'
            f'                block_explorer_url="{explorer_url}",\n'
            f'                native_currency={{"name": "{name}", "symbol": "{symbol}", "decimals": {decimals}}},\n'
            f'                features=["evm"]\n'
            f'            ),'
        )

        entries.append(entry)

    return "\n".join(entries)


async def main():
    """Generate and print registry code"""
    print("Fetching EVM chains from chainid.network...")
    chains = await fetch_chainlist_data()

    print(f"Fetched {len(chains)} chains")

    # Generate registry entries for top chains (limit to avoid too many)
    top_chains = chains[:50]  # Top 50 for manageable size

    registry_code = generate_registry_entries(top_chains)

    print("\nGenerated registry entries:")
    print(registry_code)

    print(f"\nGenerated {len(top_chains)} registry entries")


if __name__ == "__main__":
    asyncio.run(main())
