"""
Multi-Asset Payment Service
Support for ETH, USDT, USDC, BNB, MATIC, and other cryptocurrencies
"""

from typing import Dict, Optional, List
import requests
import logging
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)


class MultiAssetPaymentService:
    """Service for handling multiple cryptocurrency payments."""

    def __init__(self):
        self.supported_assets = {
            # Ethereum ecosystem
            "ETH": {"decimals": 18, "networks": ["ethereum", "polygon", "arbitrum", "optimism"]},
            "USDT": {"decimals": 6, "networks": ["ethereum", "polygon", "bsc", "arbitrum"]},
            "USDC": {"decimals": 6, "networks": ["ethereum", "polygon", "bsc", "arbitrum"]},

            # Binance Smart Chain
            "BNB": {"decimals": 18, "networks": ["bsc"]},
            "BUSD": {"decimals": 18, "networks": ["bsc"]},

            # Polygon
            "MATIC": {"decimals": 18, "networks": ["polygon"]},

            # Bitcoin
            "BTC": {"decimals": 8, "networks": ["bitcoin"]},

            # Solana
            "SOL": {"decimals": 9, "networks": ["solana"]},
        }

        self.network_configs = {
            "ethereum": {
                "chain_id": 1,
                "rpc_url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                "explorer_url": "https://etherscan.io",
                "native_currency": "ETH"
            },
            "polygon": {
                "chain_id": 137,
                "rpc_url": "https://polygon-rpc.com",
                "explorer_url": "https://polygonscan.com",
                "native_currency": "MATIC"
            },
            "bsc": {
                "chain_id": 56,
                "rpc_url": "https://bsc-dataseed.binance.org",
                "explorer_url": "https://bscscan.com",
                "native_currency": "BNB"
            },
            "arbitrum": {
                "chain_id": 42161,
                "rpc_url": "https://arb1.arbitrum.io/rpc",
                "explorer_url": "https://arbiscan.io",
                "native_currency": "ETH"
            },
            "optimism": {
                "chain_id": 10,
                "rpc_url": "https://mainnet.optimism.io",
                "explorer_url": "https://optimistic.etherscan.io",
                "native_currency": "ETH"
            },
            "bitcoin": {
                "explorer_url": "https://blockstream.info",
                "native_currency": "BTC"
            },
            "solana": {
                "rpc_url": "https://api.mainnet.solana.com",
                "explorer_url": "https://solscan.io",
                "native_currency": "SOL"
            }
        }

    def get_supported_assets(self) -> Dict[str, Dict]:
        """Get all supported assets with their configurations."""
        return self.supported_assets

    def get_supported_networks(self) -> Dict[str, Dict]:
        """Get all supported networks with their configurations."""
        return self.network_configs

    def is_asset_supported(self, asset: str, network: str) -> bool:
        """Check if asset is supported on network."""
        return asset in self.supported_assets and network in self.supported_assets[asset]["networks"]

    def get_asset_decimals(self, asset: str) -> int:
        """Get decimal places for asset."""
        return self.supported_assets.get(asset, {}).get("decimals", 18)

    def convert_to_smallest_unit(self, amount: float, asset: str) -> str:
        """Convert human-readable amount to smallest unit (wei, satoshi, etc.)."""
        decimals = self.get_asset_decimals(asset)
        smallest_unit = int(amount * (10 ** decimals))
        return str(smallest_unit)

    def convert_from_smallest_unit(self, amount: str, asset: str) -> float:
        """Convert from smallest unit to human-readable amount."""
        decimals = self.get_asset_decimals(asset)
        return int(amount) / (10 ** decimals)


class CurrencyConversionService:
    """Service for converting between currencies using real-time rates."""

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes

    def get_exchange_rate(self, from_currency: str, to_currency: str = "USD") -> float:
        """Get exchange rate from external API."""
        cache_key = f"{from_currency}_{to_currency}"

        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_timeout):
                return cached_data

        try:
            # Use CoinGecko API for rates
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={from_currency.lower()}&vs_currencies={to_currency.lower()}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            if from_currency.lower() in data and to_currency.lower() in data[from_currency.lower()]:
                rate = data[from_currency.lower()][to_currency.lower()]
                self.cache[cache_key] = (rate, datetime.utcnow())
                return rate
            else:
                logger.warning(f"Exchange rate not found for {from_currency} to {to_currency}")
                return self._get_fallback_rate(from_currency, to_currency)

        except Exception as e:
            logger.error(f"Failed to fetch exchange rate: {e}")
            return self._get_fallback_rate(from_currency, to_currency)

    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> float:
        """Fallback exchange rates when API fails."""
        fallback_rates = {
            "bitcoin": {"usd": 45000},
            "ethereum": {"usd": 3000},
            "tether": {"usd": 1.0},
            "usd-coin": {"usd": 1.0},
            "binancecoin": {"usd": 300},
            "matic-network": {"usd": 1.0},
            "solana": {"usd": 100},
        }

        from_key = from_currency.lower()
        to_key = to_currency.lower()

        if from_key in fallback_rates and to_key in fallback_rates[from_key]:
            return fallback_rates[from_key][to_key]

        # Default fallback
        return 1.0

    def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Convert amount between currencies."""
        if from_currency == to_currency:
            return amount

        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

    def usd_to_crypto(self, usd_amount: float, crypto_symbol: str) -> float:
        """Convert USD amount to cryptocurrency amount."""
        # Map common symbols to CoinGecko IDs
        coingecko_ids = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BNB": "binancecoin",
            "MATIC": "matic-network",
            "SOL": "solana",
        }

        coingecko_id = coingecko_ids.get(crypto_symbol.upper(), crypto_symbol.lower())
        rate = self.get_exchange_rate(coingecko_id, "usd")
        return usd_amount / rate if rate > 0 else 0

    def crypto_to_usd(self, crypto_amount: float, crypto_symbol: str) -> float:
        """Convert cryptocurrency amount to USD."""
        coingecko_ids = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BNB": "binancecoin",
            "MATIC": "matic-network",
            "SOL": "solana",
        }

        coingecko_id = coingecko_ids.get(crypto_symbol.upper(), crypto_symbol.lower())
        rate = self.get_exchange_rate(coingecko_id, "usd")
        return crypto_amount * rate


# Global instances
multi_asset_service = MultiAssetPaymentService()
currency_conversion_service = CurrencyConversionService()
