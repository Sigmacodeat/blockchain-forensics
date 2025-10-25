"""
NFT-Service für Blockchain-Forensik-Anwendung

Implementiert NFT-Verwaltung, Portfolio-Tracking und Metadaten-Analyse.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

# NFT-Bibliotheken (optional)
try:
    from web3 import Web3
    from eth_abi import decode_single
    import requests
    _NFT_AVAILABLE = True
except ImportError:
    _NFT_AVAILABLE = False
    logging.warning("NFT-Bibliotheken nicht verfügbar - NFT-Features werden deaktiviert")

from app.services.wallet_service import wallet_service
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class NFTMetadata:
    """NFT-Metadaten-Struktur"""

    def __init__(self, token_id: str, contract_address: str, chain: str):
        self.token_id = token_id
        self.contract_address = contract_address
        self.chain = chain
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.image_url: Optional[str] = None
        self.attributes: List[Dict[str, Any]] = []
        self.external_url: Optional[str] = None
        self.collection_name: Optional[str] = None
        self.rarity_score: Optional[float] = None
        self.last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert in Dictionary für JSON-Serialisierung"""
        return {
            "token_id": self.token_id,
            "contract_address": self.contract_address,
            "chain": self.chain,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "attributes": self.attributes,
            "external_url": self.external_url,
            "collection_name": self.collection_name,
            "rarity_score": self.rarity_score,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NFTMetadata':
        """Erstellt aus Dictionary"""
        nft = cls(
            token_id=data["token_id"],
            contract_address=data["contract_address"],
            chain=data["chain"]
        )
        nft.name = data.get("name")
        nft.description = data.get("description")
        nft.image_url = data.get("image_url")
        nft.attributes = data.get("attributes", [])
        nft.external_url = data.get("external_url")
        nft.collection_name = data.get("collection_name")
        nft.rarity_score = data.get("rarity_score")
        nft.last_updated = datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else None
        return nft

class NFTService:
    """Haupt-NFT-Service für Portfolio-Verwaltung"""

    def __init__(self):
        self.metadata_cache: Dict[str, NFTMetadata] = {}
        self.collection_cache: Dict[str, Dict[str, Any]] = {}

    async def get_nfts_for_wallet(self, wallet_address: str, chain: str) -> List[NFTMetadata]:
        """Holt alle NFTs für eine Wallet-Adresse"""
        try:
            cache_key = f"nft_portfolio_{chain}_{wallet_address}"

            # Aus Cache prüfen
            cached_data = await cache_service.get([cache_key])
            if cached_data:
                return [NFTMetadata.from_dict(nft_data) for nft_data in cached_data]

            # NFTs laden
            nfts = await self._fetch_nfts_from_chain(wallet_address, chain)

            # Metadaten laden und anreichern
            enriched_nfts = []
            for nft in nfts:
                metadata = await self._get_nft_metadata(nft, chain)
                enriched_nfts.append(metadata)

            # Im Cache speichern
            await cache_service.set([cache_key], [nft.to_dict() for nft in enriched_nfts], ttl=3600)

            return enriched_nfts

        except Exception as e:
            logger.error(f"Fehler beim Laden der NFTs für {wallet_address}: {e}")
            return []

    async def get_nft_metadata(self, contract_address: str, token_id: str, chain: str) -> Optional[NFTMetadata]:
        """Holt Metadaten für ein spezifisches NFT"""
        try:
            cache_key = f"nft_metadata_{chain}_{contract_address}_{token_id}"

            # Aus Cache prüfen
            cached_data = await cache_service.get([cache_key])
            if cached_data:
                return NFTMetadata.from_dict(cached_data)

            # Neue Metadaten laden
            metadata = await self._fetch_nft_metadata(contract_address, token_id, chain)

            # Im Cache speichern
            await cache_service.set([cache_key], metadata.to_dict(), ttl=7200)  # 2 Stunden

            return metadata

        except Exception as e:
            logger.error(f"Fehler beim Laden der NFT-Metadaten: {e}")
            return None

    async def get_collection_info(self, contract_address: str, chain: str) -> Dict[str, Any]:
        """Holt Informationen über eine NFT-Collection"""
        try:
            cache_key = f"collection_info_{chain}_{contract_address}"

            # Aus Cache prüfen
            cached_data = await cache_service.get([cache_key])
            if cached_data:
                return cached_data

            # Neue Collection-Info laden
            collection_info = await self._fetch_collection_info(contract_address, chain)

            # Im Cache speichern
            await cache_service.set([cache_key], collection_info, ttl=86400)  # 24 Stunden

            return collection_info

        except Exception as e:
            logger.error(f"Fehler beim Laden der Collection-Info: {e}")
            return {}

    async def _fetch_nfts_from_chain(self, wallet_address: str, chain: str) -> List[NFTMetadata]:
        """Holt NFTs von der Blockchain"""
        nfts = []

        try:
            if chain.lower() == "ethereum":
                nfts = await self._fetch_ethereum_nfts(wallet_address)
            elif chain.lower() == "polygon":
                nfts = await self._fetch_polygon_nfts(wallet_address)
            elif chain.lower() == "solana":
                nfts = await self._fetch_solana_nfts(wallet_address)
            else:
                logger.warning(f"NFT-Unterstützung für Chain {chain} nicht implementiert")

        except Exception as e:
            logger.error(f"Fehler beim Laden der NFTs von {chain}: {e}")

        return nfts

    async def _fetch_ethereum_nfts(self, wallet_address: str) -> List[NFTMetadata]:
        """Holt Ethereum-NFTs"""
        nfts = []

        try:
            # Hier würde echte Ethereum-NFT-Abfrage implementiert werden
            # Für Demo: Simulierte NFTs
            sample_nfts = [
                {"contract_address": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D", "token_id": "1"},
                {"contract_address": "0x60E4d786628Fea6478F785A6d7e704777c86a7c6", "token_id": "2"},
                {"contract_address": "0x49cF6f5d44E70224e2E23fDcdd2C053F30aDA28B", "token_id": "3"}
            ]

            for nft_data in sample_nfts:
                nft = NFTMetadata(
                    token_id=nft_data["token_id"],
                    contract_address=nft_data["contract_address"],
                    chain="ethereum"
                )
                nfts.append(nft)

        except Exception as e:
            logger.error(f"Fehler beim Laden der Ethereum-NFTs: {e}")

        return nfts

    async def _fetch_polygon_nfts(self, wallet_address: str) -> List[NFTMetadata]:
        """Holt Polygon-NFTs"""
        # Ähnliche Implementierung für Polygon
        return []

    async def _fetch_solana_nfts(self, wallet_address: str) -> List[NFTMetadata]:
        """Holt Solana-NFTs"""
        # Ähnliche Implementierung für Solana
        return []

    async def _fetch_nft_metadata(self, contract_address: str, token_id: str, chain: str) -> NFTMetadata:
        """Holt detaillierte NFT-Metadaten"""
        nft = NFTMetadata(token_id, contract_address, chain)

        try:
            # Token-URI von Smart Contract holen
            token_uri = await self._get_token_uri(contract_address, token_id, chain)

            if token_uri:
                # Metadaten von URI laden
                metadata = await self._fetch_metadata_from_uri(token_uri)

                nft.name = metadata.get("name")
                nft.description = metadata.get("description")
                nft.image_url = metadata.get("image")
                nft.attributes = metadata.get("attributes", [])
                nft.external_url = metadata.get("external_url")

                # Collection-Name aus Attributen extrahieren
                for attr in nft.attributes:
                    if attr.get("trait_type", "").lower() == "collection":
                        nft.collection_name = attr.get("value")

                # Rarity-Score berechnen (vereinfacht)
                nft.rarity_score = await self._calculate_rarity_score(nft.attributes)

            nft.last_updated = datetime.utcnow()

        except Exception as e:
            logger.error(f"Fehler beim Laden der NFT-Metadaten: {e}")

        return nft

    async def _get_token_uri(self, contract_address: str, token_id: str, chain: str) -> Optional[str]:
        """Holt Token-URI von Smart Contract"""
        try:
            if chain.lower() == "ethereum":
                # Ethereum Smart Contract aufrufen
                # Hier würde Web3.py verwendet werden
                # Für Demo: Simulierte URI
                return f"https://api.example.com/metadata/{contract_address}/{token_id}"
            else:
                return None

        except Exception as e:
            logger.error(f"Fehler beim Laden der Token-URI: {e}")
            return None

    async def _fetch_metadata_from_uri(self, uri: str) -> Dict[str, Any]:
        """Holt Metadaten von URI"""
        try:
            # HTTP-Request für Metadaten
            # Für Demo: Simulierte Metadaten
            return {
                "name": "Sample NFT",
                "description": "A sample NFT for demonstration",
                "image": "https://example.com/image.png",
                "attributes": [
                    {"trait_type": "Background", "value": "Blue"},
                    {"trait_type": "Rarity", "value": "Common"}
                ]
            }

        except Exception as e:
            logger.error(f"Fehler beim Laden der Metadaten von {uri}: {e}")
            return {}

    async def _fetch_collection_info(self, contract_address: str, chain: str) -> Dict[str, Any]:
        """Holt Collection-Informationen"""
        try:
            # Collection-Daten laden
            return {
                "name": "Sample NFT Collection",
                "description": "A collection of sample NFTs",
                "total_supply": 10000,
                "floor_price": 0.1,
                "volume_traded": 1500.5,
                "owners": 2500
            }

        except Exception as e:
            logger.error(f"Fehler beim Laden der Collection-Info: {e}")
            return {}

    async def _calculate_rarity_score(self, attributes: List[Dict[str, Any]]) -> float:
        """Berechnet Rarity-Score basierend auf Attributen"""
        try:
            if not attributes:
                return 0.5

            # Vereinfachte Rarity-Berechnung
            total_traits = len(attributes)
            rare_traits = sum(1 for attr in attributes if attr.get("rarity", 1) < 0.1)

            return min(1.0, (rare_traits / total_traits) * 2)

        except Exception as e:
            logger.error(f"Fehler bei Rarity-Berechnung: {e}")
            return 0.5

class NFTPortfolioAnalyzer:
    """Analyzer für NFT-Portfolio-Analyse"""

    def __init__(self):
        self.nft_service = NFTService()

    async def analyze_portfolio(self, wallet_address: str, chain: str) -> Dict[str, Any]:
        """Führt umfassende Portfolio-Analyse durch"""
        try:
            # NFTs laden
            nfts = await self.nft_service.get_nfts_for_wallet(wallet_address, chain)

            # Portfolio-Metriken berechnen
            total_value = 0
            rarity_distribution = {"common": 0, "uncommon": 0, "rare": 0, "legendary": 0}
            collections = {}

            for nft in nfts:
                # Wert schätzen (vereinfacht)
                estimated_value = await self._estimate_nft_value(nft)
                total_value += estimated_value

                # Rarity-Kategorisierung
                rarity = self._categorize_rarity(nft.rarity_score or 0)
                rarity_distribution[rarity] += 1

                # Collections zählen
                collection = nft.collection_name or "Unknown"
                collections[collection] = collections.get(collection, 0) + 1

            # Portfolio-Score berechnen
            portfolio_score = self._calculate_portfolio_score(nfts, total_value)

            return {
                "wallet_address": wallet_address,
                "chain": chain,
                "total_nfts": len(nfts),
                "total_value": total_value,
                "portfolio_score": portfolio_score,
                "rarity_distribution": rarity_distribution,
                "collections": collections,
                "top_collections": self._get_top_collections(collections),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Portfolio-Analyse fehlgeschlagen: {e}")
            return {
                "error": str(e),
                "wallet_address": wallet_address,
                "chain": chain
            }

    async def _estimate_nft_value(self, nft: NFTMetadata) -> float:
        """Schätzt den Wert eines NFT"""
        try:
            # Basis-Wert basierend auf Rarity
            base_value = 0.1  # ETH

            if nft.rarity_score:
                rarity_multiplier = 1 + (nft.rarity_score * 10)
                base_value *= rarity_multiplier

            # Collection-basierter Bonus
            if nft.collection_name:
                collection_info = await self.nft_service.get_collection_info(
                    nft.contract_address, nft.chain
                )
                floor_price = collection_info.get("floor_price", 0)
                if floor_price > 0:
                    base_value = max(base_value, floor_price)

            return base_value

        except Exception as e:
            logger.error(f"Wertschätzung fehlgeschlagen: {e}")
            return 0.1

    def _categorize_rarity(self, rarity_score: float) -> str:
        """Kategorisiert Rarity-Score"""
        if rarity_score >= 0.8:
            return "legendary"
        elif rarity_score >= 0.5:
            return "rare"
        elif rarity_score >= 0.2:
            return "uncommon"
        else:
            return "common"

    def _calculate_portfolio_score(self, nfts: List[NFTMetadata], total_value: float) -> float:
        """Berechnet Portfolio-Score"""
        try:
            if not nfts:
                return 0.0

            # Durchschnittliche Rarity
            avg_rarity = sum(nft.rarity_score or 0 for nft in nfts) / len(nfts)

            # Diversifikation (verschiedene Collections)
            unique_collections = len(set(nft.collection_name or "Unknown" for nft in nfts))
            diversification_score = min(1.0, unique_collections / 10)  # Max 10 Collections

            # Kombinierter Score
            portfolio_score = (avg_rarity * 0.6) + (diversification_score * 0.4)

            return min(1.0, portfolio_score)

        except Exception as e:
            logger.error(f"Portfolio-Score-Berechnung fehlgeschlagen: {e}")
            return 0.5

    def _get_top_collections(self, collections: Dict[str, int], limit: int = 5) -> List[Dict[str, Any]]:
        """Holt Top-Collections nach Anzahl"""
        sorted_collections = sorted(
            collections.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"name": name, "count": count}
            for name, count in sorted_collections[:limit]
        ]

# Singleton-Instances
nft_service = NFTService()
nft_analyzer = NFTPortfolioAnalyzer()
