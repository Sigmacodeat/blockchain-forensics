"""
Wallet Seed Phrase Scanner Service (Chainalysis Wallet Scan)

Scan seed phrases/private keys for balances, activity, and illicit connections.
Similar to Chainalysis Wallet Scan feature.

Features:
- Multi-chain balance checking
- Historical activity analysis
- Illicit connection detection
- Risk scoring
- Asset recovery assistance
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import asyncio

# Integrationen ins bestehende System
from app.services.multi_chain import ChainAdapterFactory  # nutzt Adapter pro Chain
from app.enrichment.labels_service import labels_service  # Labels/Sanctions/Exchange

# BIP39/BIP44 Derivation
try:
    from mnemonic import Mnemonic
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()
    _MNEMONIC_AVAILABLE = True
except ImportError:
    _MNEMONIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class WalletType(str, Enum):
    """Type of wallet credentials"""
    SEED_PHRASE = "seed_phrase"
    PRIVATE_KEY = "private_key"
    KEYSTORE = "keystore"
    HARDWARE_WALLET = "hardware_wallet"


class ActivityLevel(str, Enum):
    """Level of wallet activity"""
    DORMANT = "dormant"  # No activity in 6+ months
    LOW = "low"  # 1-10 txs/month
    MODERATE = "moderate"  # 10-100 txs/month
    HIGH = "high"  # 100-1000 txs/month
    VERY_HIGH = "very_high"  # 1000+ txs/month


class WalletScannerService:
    """
    Wallet Scanner Service for seed phrase/private key analysis.
    
    Security:
    - Seeds/keys never stored
    - Processed in-memory only
    - Audit logging for compliance
    - Optional encryption at rest
    """
    
    def __init__(self):
        self.scan_cache: Dict[str, Dict[str, Any]] = {}  # Temporary cache
        
    async def scan_seed_phrase(
        self,
        seed_phrase: str,
        chains: Optional[List[str]] = None,
        check_history: bool = True,
        check_illicit: bool = True,
        derivation_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scan a seed phrase for balances and activity.
        
        Args:
            seed_phrase: BIP39 seed phrase (12/24 words)
            chains: Chains to check (default: all major)
            check_history: Check transaction history
            check_illicit: Check for illicit connections
            derivation_paths: Custom derivation paths
            
        Returns:
            Comprehensive scan results
        """
        # Validate seed phrase
        if not self._validate_seed_phrase(seed_phrase):
            raise ValueError("Invalid seed phrase format")
        
        # Generate scan ID (hashed for privacy)
        scan_id = self._generate_scan_id(seed_phrase)
        
        # Check cache (TTL: 5 minutes)
        if scan_id in self.scan_cache:
            cached = self.scan_cache[scan_id]
            if (datetime.utcnow() - datetime.fromisoformat(cached["scanned_at"])).seconds < 300:
                logger.info(f"Returning cached scan: {scan_id}")
                return cached
        
        chains = chains or ["ethereum", "bitcoin", "polygon", "bsc", "arbitrum"]
        derivation_paths = derivation_paths or self._get_default_paths()
        
        # Derive addresses for each chain
        addresses = await self._derive_addresses(seed_phrase, chains, derivation_paths)
        
        # Scan each address
        scan_tasks = []
        for chain, addrs in addresses.items():
            for addr_info in addrs:
                scan_tasks.append(
                    self._scan_address(
                        chain=chain,
                        address=addr_info["address"],
                        derivation_path=addr_info["path"],
                        check_history=check_history,
                        check_illicit=check_illicit
                    )
                )
        
        results = await asyncio.gather(*scan_tasks)
        
        # Aggregate results
        aggregated = self._aggregate_results(results, addresses)
        
        # Add metadata
        scan_result = {
            "scan_id": scan_id,
            "wallet_type": WalletType.SEED_PHRASE.value,
            "scanned_at": datetime.utcnow().isoformat(),
            "chains_scanned": chains,
            "total_addresses": sum(len(addrs) for addrs in addresses.values()),
            "total_balance_usd": aggregated["total_balance_usd"],
            "total_transactions": aggregated["total_transactions"],
            "activity_level": aggregated["activity_level"],
            "risk_score": aggregated["risk_score"],
            "illicit_connections": aggregated["illicit_connections"],
            "addresses": aggregated["addresses"],
            "recommendations": aggregated["recommendations"]
        }
        
        # Cache result (with TTL)
        self.scan_cache[scan_id] = scan_result
        
        logger.info(f"Wallet scan completed: {scan_id} - Balance: ${aggregated['total_balance_usd']}")
        
        return scan_result
    
    async def scan_private_key(
        self,
        private_key: str,
        chain: str,
        check_history: bool = True,
        check_illicit: bool = True
    ) -> Dict[str, Any]:
        """
        Scan a single private key.
        
        Args:
            private_key: Private key (hex)
            chain: Chain to check
            check_history: Check transaction history
            check_illicit: Check for illicit connections
            
        Returns:
            Scan results for single address
        """
        # Validate private key
        if not self._validate_private_key(private_key):
            raise ValueError("Invalid private key format")
        
        # Derive address
        address = await self._derive_address_from_key(private_key, chain)
        
        # Scan address
        result = await self._scan_address(
            chain=chain,
            address=address,
            derivation_path="direct",
            check_history=check_history,
            check_illicit=check_illicit
        )
        
        scan_id = self._generate_scan_id(private_key)
        
        return {
            "scan_id": scan_id,
            "wallet_type": WalletType.PRIVATE_KEY.value,
            "scanned_at": datetime.utcnow().isoformat(),
            "chain": chain,
            "address": address,
            **result
        }
    
    async def _scan_address(
        self,
        chain: str,
        address: str,
        derivation_path: str,
        check_history: bool = True,
        check_illicit: bool = True
    ) -> Dict[str, Any]:
        """Scan a single address mit Live-Daten (Adapter/Labels)."""
        try:
            adapter = ChainAdapterFactory().get_adapter(chain)
        except Exception as _adp_err:
            logger.warning(f"Adapter resolution failed for {chain}: {_adp_err}")
            adapter = None
        if not adapter:
            return {
                "chain": chain,
                "address": address,
                "derivation_path": derivation_path,
                "balance": {"native": 0.0, "usd": 0.0, "tokens": []},
                "transaction_count": 0,
                "first_seen": None,
                "last_seen": None,
                "activity_level": ActivityLevel.DORMANT.value,
                "risk_score": 0.0,
                "illicit_connections": [],
                "labels": ["unsupported_chain"],
            }

        # Preise (vereinfachte Map, bis price_service verfügbar ist)
        price_map: Dict[str, float] = {
            "ethereum": 2000.0,
            "polygon": 1.0,
            "bsc": 300.0,
            "arbitrum": 2000.0,
            "optimism": 2000.0,
            "base": 2000.0,
            "bitcoin": 60000.0,
            "solana": 100.0,
        }

        native_price_usd = price_map.get(chain, 1.0)

        # Balance & Transaktionen
        txs: List[Dict[str, Any]] = []
        tx_count = 0
        first_seen = None
        last_seen = None
        import os
        if os.getenv("TEST_MODE") == "1":
            # Keine externen RPC-Calls in Tests
            balance_native = 0.0
            txs = []
            tx_count = 0
        else:
            try:
                balance_native = await adapter.get_address_balance(address)
            except Exception:
                balance_native = 0.0

            if check_history:
                try:
                    txs = await adapter.get_address_transactions(address, limit=100)
                    tx_count = len(txs)
                    if txs:
                        # Versuche Zeitfelder zu erkennen (EVM: timestamp, BTC: timestamp, SVM: block_time)
                        timestamps = [
                            t.get("timestamp") or t.get("block_time") for t in txs if (t.get("timestamp") or t.get("block_time")) is not None
                        ]
                        if timestamps:
                            first_seen = datetime.utcfromtimestamp(min(timestamps)).isoformat() if isinstance(timestamps[0], (int, float)) else None
                            last_seen = datetime.utcfromtimestamp(max(timestamps)).isoformat() if isinstance(timestamps[0], (int, float)) else None
                except Exception:
                    txs = []
                    tx_count = 0

        # Aktivitätslevel bestimmen
        if tx_count == 0:
            activity_level = ActivityLevel.DORMANT.value
        elif tx_count < 10:
            activity_level = ActivityLevel.LOW.value
        elif tx_count < 100:
            activity_level = ActivityLevel.MODERATE.value
        elif tx_count < 1000:
            activity_level = ActivityLevel.HIGH.value
        else:
            activity_level = ActivityLevel.VERY_HIGH.value

        # Labels / Illicit
        labels: List[str] = []
        illicit_connections: List[Dict[str, Any]] = []
        try:
            labels = await labels_service.get_labels(address)
        except Exception:
            labels = []

        if check_illicit and labels:
            if any(l in ("sanctioned", "ofac") for l in labels):
                illicit_connections.append({
                    "address": address,
                    "chain": chain,
                    "type": "sanctioned",
                    "risk_score": 0.95,
                })
            if any(l in ("mixer", "tornado", "blender") for l in labels):
                illicit_connections.append({
                    "address": address,
                    "chain": chain,
                    "type": "mixer",
                    "risk_score": 0.85,
                })

        # Einfache Risikoabschätzung (kombiniert Labels + Aktivität + Balance)
        risk_base = 0.0
        if any(l in ("sanctioned", "ofac") for l in labels):
            risk_base = max(risk_base, 0.95)
        if any(l in ("scam", "high_risk") for l in labels):
            risk_base = max(risk_base, 0.7)
        if any(l in ("exchange",) for l in labels):
            risk_base = max(risk_base, 0.2)
        # Aktivitätsgewichtung
        activity_weight = {
            ActivityLevel.DORMANT.value: 0.0,
            ActivityLevel.LOW.value: 0.05,
            ActivityLevel.MODERATE.value: 0.1,
            ActivityLevel.HIGH.value: 0.2,
            ActivityLevel.VERY_HIGH.value: 0.3,
        }.get(activity_level, 0.0)
        # Balance-Gewichtung (logarithmisch vereinfacht)
        balance_usd = balance_native * native_price_usd
        balance_weight = 0.0
        if balance_usd > 0:
            balance_weight = min(0.3, 0.05 + (balance_usd / 100000.0))  # +0.05 bis max 0.3

        risk_score = min(1.0, risk_base + activity_weight + balance_weight)
        if risk_score >= 0.9:
            risk_level = "critical"
        elif risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "chain": chain,
            "address": address,
            "derivation_path": derivation_path,
            "balance": {
                "native": balance_native,
                "usd": balance_usd,
                "tokens": []  # Token-Scan kann später via ERC20/NFT ergänzt werden
            },
            "transaction_count": tx_count,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "activity_level": activity_level,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "illicit_connections": illicit_connections,
            "labels": labels,
        }
    
    async def _derive_addresses(
        self,
        seed_phrase: str,
        chains: List[str],
        derivation_paths: List[str]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Derive addresses from seed phrase for multiple chains.
        
        Returns:
            {chain: [{"address": ..., "path": ...}, ...]}
        """
        addresses = {}
        
        if not _MNEMONIC_AVAILABLE:
            logger.warning("mnemonic/eth_account not available, using placeholder")
            for chain in chains:
                chain_addrs = []
                for path in derivation_paths:
                    addr = f"0x{'0' * 40}"
                    chain_addrs.append({"address": addr, "path": path})
                addresses[chain] = chain_addrs
            return addresses
        
        # Validate mnemonic
        try:
            mnemo = Mnemonic("english")
            if not mnemo.check(seed_phrase):
                raise ValueError("Invalid seed phrase")
        except Exception as e:
            logger.error(f"Seed validation failed: {e}")
            raise ValueError("Invalid seed phrase")
        
        for chain in chains:
            chain_addrs = []
            for path in derivation_paths:
                try:
                    if chain in ("ethereum", "polygon", "bsc", "arbitrum", "optimism", "base", "avalanche"):
                        # EVM: m/44'/60'/0'/0/0
                        acct = Account.from_mnemonic(seed_phrase, account_path=path)
                        addr = acct.address
                    elif chain == "bitcoin":
                        # BTC: placeholder (braucht separate BTC lib wie bip_utils)
                        addr = f"bc1q{'0' * 38}"
                    elif chain == "solana":
                        # Solana: placeholder (braucht solana-py + derivation)
                        addr = f"{'1' * 44}"
                    else:
                        addr = f"0x{'0' * 40}"
                    chain_addrs.append({"address": addr, "path": path})
                except Exception as e:
                    logger.warning(f"Derivation failed for {chain} {path}: {e}")
                    chain_addrs.append({"address": f"0x{'0' * 40}", "path": path})
            addresses[chain] = chain_addrs
        
        return addresses
    
    async def _derive_address_from_key(
        self,
        private_key: str,
        chain: str
    ) -> str:
        """Derive address from private key."""
        if not _MNEMONIC_AVAILABLE:
            return f"0x{'0' * 40}"
        
        try:
            # Normalisiere Hex-Key (entferne 0x prefix falls vorhanden)
            pk = private_key.strip()
            if pk.startswith("0x"):
                pk = pk[2:]
            
            if chain in ("ethereum", "polygon", "bsc", "arbitrum", "optimism", "base", "avalanche"):
                acct = Account.from_key(f"0x{pk}")
                return acct.address
            elif chain == "bitcoin":
                # BTC: placeholder
                return f"bc1q{'0' * 38}"
            elif chain == "solana":
                # Solana: placeholder
                return f"{'1' * 44}"
            else:
                return f"0x{'0' * 40}"
        except Exception as e:
            logger.error(f"Private key derivation failed for {chain}: {e}")
            raise ValueError("Invalid private key")

    async def scan_addresses(
        self,
        addrs: List[Dict[str, str]],
        check_history: bool = True,
        check_illicit: bool = True,
    ) -> Dict[str, Any]:
        """
        Zero-Trust: Scanne bereits abgeleitete Adressen (kein Seed/Key nötig).

        Args:
            addrs: Liste von {chain, address}
        Returns:
            Aggregiertes Scan-Result analog zu scan_seed_phrase
        """
        if not addrs:
            return {
                "scan_id": f"scan-{hashlib.sha256(b'empty').hexdigest()[:16]}",
                "wallet_type": "addresses",
                "scanned_at": datetime.utcnow().isoformat(),
                "chains_scanned": [],
                "total_addresses": 0,
                "total_balance_usd": 0.0,
                "total_transactions": 0,
                "activity_level": ActivityLevel.DORMANT.value,
                "risk_score": 0.0,
                "illicit_connections": [],
                "addresses": [],
                "recommendations": ["No addresses provided"],
            }

        tasks: List[asyncio.Task] = []
        for item in addrs:
            c = item.get("chain", "ethereum")
            a = item.get("address", "").strip()
            if not a:
                continue
            tasks.append(self._scan_address(c, a, derivation_path="direct", check_history=check_history, check_illicit=check_illicit))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid = [r for r in results if isinstance(r, dict)]

        aggregated = self._aggregate_results(valid, {})
        scan_id = f"scan-{hashlib.sha256((';'.join([v['address'] for v in valid]) or 'addr').encode()).hexdigest()[:16]}"
        return {
            "scan_id": scan_id,
            "wallet_type": "addresses",
            "scanned_at": datetime.utcnow().isoformat(),
            "chains_scanned": list({v["chain"] for v in valid}),
            "total_addresses": len(valid),
            "total_balance_usd": aggregated["total_balance_usd"],
            "total_transactions": aggregated["total_transactions"],
            "activity_level": aggregated["activity_level"],
            "risk_score": aggregated["risk_score"],
            "illicit_connections": aggregated["illicit_connections"],
            "addresses": valid,
            "recommendations": aggregated["recommendations"],
        }
    
    def _aggregate_results(
        self,
        results: List[Dict[str, Any]],
        addresses: Dict[str, List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        """Aggregate scan results."""
        total_balance_usd = sum(r["balance"]["usd"] for r in results)
        total_transactions = sum(r["transaction_count"] for r in results)
        
        # Determine activity level
        avg_txs_per_month = total_transactions / max(len(results), 1) / 12  # Rough estimate
        if avg_txs_per_month == 0:
            activity_level = ActivityLevel.DORMANT.value
        elif avg_txs_per_month < 10:
            activity_level = ActivityLevel.LOW.value
        elif avg_txs_per_month < 100:
            activity_level = ActivityLevel.MODERATE.value
        elif avg_txs_per_month < 1000:
            activity_level = ActivityLevel.HIGH.value
        else:
            activity_level = ActivityLevel.VERY_HIGH.value
        
        # Aggregate risk
        max_risk = max((r["risk_score"] for r in results), default=0.0)
        
        # Collect illicit connections
        illicit_connections = []
        for r in results:
            illicit_connections.extend(r["illicit_connections"])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            total_balance_usd,
            activity_level,
            max_risk,
            illicit_connections
        )
        
        return {
            "total_balance_usd": total_balance_usd,
            "total_transactions": total_transactions,
            "activity_level": activity_level,
            "risk_score": max_risk,
            "illicit_connections": illicit_connections,
            "addresses": results,
            "recommendations": recommendations
        }
    
    def _generate_recommendations(
        self,
        balance: float,
        activity: str,
        risk: float,
        illicit: List[Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if balance > 0:
            recs.append(f"Assets found: ${balance:.2f} USD")
            recs.append("Consider moving funds to a secure wallet")
        
        if activity == ActivityLevel.DORMANT.value and balance > 0:
            recs.append("Wallet is dormant but contains funds - check for recovery")
        
        if risk >= 0.7:
            recs.append("⚠️ HIGH RISK - Address has illicit connections")
            recs.append("Contact compliance team before moving funds")
        elif risk >= 0.4:
            recs.append("⚠️ MEDIUM RISK - Enhanced due diligence recommended")
        
        if illicit:
            recs.append(f"⚠️ {len(illicit)} illicit connection(s) detected")
            recs.append("Review flagged transactions before proceeding")
        
        if not balance and activity == ActivityLevel.DORMANT.value:
            recs.append("No assets or activity detected")
        
        return recs
    
    def _validate_seed_phrase(self, seed_phrase: str) -> bool:
        """Validate BIP39 seed phrase."""
        words = seed_phrase.strip().split()
        return len(words) in [12, 15, 18, 21, 24]
    
    def _validate_private_key(self, private_key: str) -> bool:
        """Validate private key format."""
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        return len(private_key) == 64 and all(c in "0123456789abcdefABCDEF" for c in private_key)
    
    def _get_default_paths(self) -> List[str]:
        """Get default BIP44 derivation paths."""
        return [
            "m/44'/60'/0'/0/0",  # Ethereum first address
            "m/44'/60'/0'/0/1",  # Ethereum second address
            "m/44'/60'/0'/0/2",  # Ethereum third address
            "m/44'/0'/0'/0/0",   # Bitcoin first address
            "m/44'/0'/0'/0/1",   # Bitcoin second address
        ]
    
    def _generate_scan_id(self, credential: str) -> str:
        """Generate privacy-preserving scan ID."""
        return f"scan-{hashlib.sha256(credential.encode()).hexdigest()[:16]}"
    
    async def bulk_scan(
        self,
        credentials: List[Dict[str, Any]],
        chains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Bulk scan multiple wallets (for asset recovery).
        
        Args:
            credentials: List of {type, value} dicts
            chains: Chains to check
            
        Returns:
            List of scan results
        """
        tasks = []
        
        for cred in credentials:
            if cred["type"] == WalletType.SEED_PHRASE.value:
                tasks.append(
                    self.scan_seed_phrase(
                        seed_phrase=cred["value"],
                        chains=chains,
                        check_history=False,  # Skip for bulk
                        check_illicit=True
                    )
                )
            elif cred["type"] == WalletType.PRIVATE_KEY.value:
                for chain in (chains or ["ethereum"]):
                    tasks.append(
                        self.scan_private_key(
                            private_key=cred["value"],
                            chain=chain,
                            check_history=False,
                            check_illicit=True
                        )
                    )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        logger.info(f"Bulk scan completed: {len(valid_results)}/{len(credentials)} successful")
        
        return valid_results


# Global service instance
wallet_scanner_service = WalletScannerService()
