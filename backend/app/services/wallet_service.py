"""
Wallet Service für Blockchain-Forensik-Plattform

Integriert Trust Wallet Core für Multi-Chain-Wallet-Funktionalität
mit Forensik-spezifischen Features.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import asyncio
from decimal import Decimal

# Trust Wallet Core Integration (C++ Bindings)
try:
    from wallet_core import WalletCore, CoinType, HDWallet, PrivateKey, PublicKey
    _WALLET_CORE_AVAILABLE = True
except ImportError:
    _WALLET_CORE_AVAILABLE = False
    logging.warning("Trust Wallet Core nicht verfügbar - Wallet-Features werden deaktiviert")

from app.config import settings
from app.db.session import get_db
# from app.services.ai_agent_service import AIAgentService  # TODO: Implement AI Agent Service

logger = logging.getLogger(__name__)

class WalletService:
    """Haupt-Wallet-Service für Multi-Chain-Operationen"""

    def __init__(self):
        self.wallet_core = WalletCore() if _WALLET_CORE_AVAILABLE else None
        # self.ai_agent = AIAgentService()  # TODO: Implement AI Agent Service
        self.ai_agent = None
        self.wallet_data_dir = Path(settings.WALLET_DATA_DIR or "data/wallets")
        self.wallet_data_dir.mkdir(exist_ok=True)

    async def create_wallet(self, chain: str, mnemonic: Optional[str] = None) -> Dict[str, Any]:
        """Erstellt eine neue Wallet für eine spezifische Chain"""
        if not self.wallet_core:
            raise RuntimeError("Wallet Core nicht verfügbar")

        try:
            # HD Wallet erstellen
            if not mnemonic:
                hd_wallet = HDWallet(strength=256)  # 24 Wörter
                mnemonic = hd_wallet.mnemonic()
            else:
                hd_wallet = HDWallet(mnemonic=mnemonic)

            # Chain-spezifische Adresse generieren
            coin_type = self._get_coin_type(chain)
            private_key = hd_wallet.getKeyForCoin(coin_type)
            public_key = private_key.getPublicKeySecp256k1(False)
            address = self._get_address_from_public_key(chain, public_key)

            wallet_data = {
                "id": f"wallet_{chain}_{address[:8]}",
                "chain": chain,
                "address": address,
                "public_key": public_key.data().hex(),
                "mnemonic": mnemonic,  # Nur für interne Verwendung speichern
                "created_at": asyncio.get_event_loop().time(),
                "balance": await self.get_balance(chain, address),
                "transactions": []
            }

            # Wallet-Daten speichern
            await self._save_wallet_data(wallet_data)

            return wallet_data

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Wallet: {e}")
            raise

    async def get_balance(self, chain: str, address: str) -> Dict[str, Any]:
        """Holt den Kontostand für eine Adresse (Multi-Chain Adapter)."""
        try:
            from app.adapters import get_adapter
            adapter = get_adapter(chain)
            if not adapter:
                return {"balance": "0", "error": f"Chain {chain} nicht unterstützt"}

            # Multi-Chain Adapter verwenden (get_address_balance)
            try:
                balance_val = await adapter.get_address_balance(address)
            except AttributeError:
                # Fallback für alte Adapter-Signatur
                balance_val = await adapter.get_balance(address)  # type: ignore[attr-defined]

            # KI-Risikoanalyse
            risk_analysis = await self.ai_agent.analyze_wallet_risk(
                chain=chain,
                address=address,
                balance=balance_val
            )

            return {
                "balance": balance_val,
                "risk_score": risk_analysis.get("risk_score", 0),
                "risk_factors": risk_analysis.get("risk_factors", []),
                "last_updated": asyncio.get_event_loop().time()
            }

        except Exception as e:
            logger.error(f"Fehler beim Holen des Balances: {e}")
            return {"balance": "0", "error": str(e)}

    async def sign_transaction(self, chain: str, tx_data: Dict[str, Any],
                              private_key_hex: str) -> Dict[str, Any]:
        """Signiert eine Transaktion"""
        if not self.wallet_core:
            raise RuntimeError("Wallet Core nicht verfügbar")

        try:
            # Private Key laden
            private_key = PrivateKey(data=bytes.fromhex(private_key_hex))

            # Chain-spezifisches Signing
            coin_type = self._get_coin_type(chain)

            if chain.lower() == "ethereum":
                return await self._sign_ethereum_tx(tx_data, private_key, coin_type)
            elif chain.lower() == "bitcoin":
                return await self._sign_bitcoin_tx(tx_data, private_key, coin_type)
            elif chain.lower() == "solana":
                return await self._sign_solana_tx(tx_data, private_key, coin_type)
            else:
                raise ValueError(f"Signing für Chain {chain} nicht implementiert")

        except Exception as e:
            logger.error(f"Fehler beim Signieren der Transaktion: {e}")
            raise

    async def broadcast_transaction(self, chain: str, signed_tx: str) -> Dict[str, Any]:
        """Broadcastet eine signierte Transaktion via Chain-RPC (Multi-Chain)."""
        try:
            from app.adapters import get_adapter
            adapter = get_adapter(chain)
            if not adapter:
                raise ValueError(f"Chain {chain} nicht unterstützt")

            # Normalisiere Payload
            def _ensure_0x(hex_str: str) -> str:
                return hex_str if hex_str.startswith("0x") else ("0x" + hex_str)

            async def _send_raw_evm(tx_hex: str) -> str:
                payload = await adapter.make_request("eth_sendRawTransaction", [_ensure_0x(tx_hex)])
                result = payload.get("result")
                if not result:
                    err = payload.get("error") or {}
                    raise RuntimeError(f"RPC error: {err}")
                return str(result)

            async def _send_raw_btc(tx_hex: str) -> str:
                payload = await adapter.make_request("sendrawtransaction", [tx_hex])
                result = payload.get("result")
                if not result:
                    err = payload.get("error") or {}
                    raise RuntimeError(f"RPC error: {err}")
                return str(result)

            def _hex_to_base64(tx_hex: str) -> str:
                import base64, binascii
                b = binascii.unhexlify(tx_hex[2:] if tx_hex.startswith("0x") else tx_hex)
                return base64.b64encode(b).decode("ascii")

            async def _send_raw_solana(tx_hex: str) -> str:
                # Solana sendTransaction erwartet base64
                base64_tx = _hex_to_base64(tx_hex)
                payload = await adapter.make_request("sendTransaction", [base64_tx, {"encoding": "base64"}])
                result = payload.get("result")
                if not result:
                    err = payload.get("error") or {}
                    raise RuntimeError(f"RPC error: {err}")
                return str(result)

            chain_l = chain.lower()
            if chain_l in {"ethereum", "polygon", "bsc", "avalanche", "arbitrum", "optimism"}:
                tx_hash = await _send_raw_evm(signed_tx)
            elif chain_l == "bitcoin":
                tx_hash = await _send_raw_btc(signed_tx)
            elif chain_l == "solana":
                tx_hash = await _send_raw_solana(signed_tx)
            else:
                raise ValueError(f"Broadcast für Chain {chain} nicht implementiert")

            # KI-Analyse
            analysis = await self.ai_agent.analyze_transaction(
                chain=chain,
                tx_hash=tx_hash,
                tx_type="outgoing"
            )

            return {
                "tx_hash": tx_hash,
                "status": "broadcasted",
                "analysis": analysis,
                "timestamp": asyncio.get_event_loop().time()
            }

        except Exception as e:
            logger.error(f"Fehler beim Broadcasten der Transaktion: {e}")
            raise

    async def get_wallet_history(self, chain: str, address: str) -> List[Dict[str, Any]]:
        """Holt die Transaktionshistorie einer Wallet (Multi-Chain Adapter)."""
        try:
            from app.adapters import get_adapter
            adapter = get_adapter(chain)
            if not adapter:
                return []

            try:
                transactions = await adapter.get_address_transactions(address, limit=100)
            except AttributeError:
                transactions = await adapter.get_transaction_history(address)  # type: ignore[attr-defined]

            analyzed_txs = []
            for tx in transactions:
                tx_hash = tx.get("hash") or tx.get("tx_hash") or tx.get("tx_signature") or ""
                to_addr = tx.get("to") or tx.get("to_address")
                direction = "incoming" if (to_addr and str(to_addr).lower() == str(address).lower()) else "outgoing"
                analysis = await self.ai_agent.analyze_transaction(
                    chain=chain,
                    tx_hash=str(tx_hash),
                    tx_type=direction
                )
                tx["analysis"] = analysis
                analyzed_txs.append(tx)

            return analyzed_txs

        except Exception as e:
            logger.error(f"Fehler beim Laden der Wallet-Historie: {e}")
            return []

    def _get_coin_type(self, chain: str) -> int:
        """Mappt Chain-Namen auf CoinType"""
        if not _WALLET_CORE_AVAILABLE:
            # Fallback wenn Wallet Core nicht verfügbar
            chain_map = {
                "ethereum": 60, "bitcoin": 0, "solana": 501, "polygon": 60,
                "bsc": 60, "avalanche": 60, "arbitrum": 60, "optimism": 60,
            }
            return chain_map.get(chain.lower(), 60)
        
        chain_map = {
            "ethereum": CoinType.ETHEREUM,
            "bitcoin": CoinType.BITCOIN,
            "solana": CoinType.SOLANA,
            "polygon": CoinType.POLYGON,
            "bsc": CoinType.SMARTCHAIN,
            "avalanche": CoinType.AVALANCHE,
            "arbitrum": CoinType.ARBITRUM,
            "optimism": CoinType.OPTIMISM,
        }
        return chain_map.get(chain.lower(), CoinType.ETHEREUM)

    def _get_address_from_public_key(self, chain: str, public_key: 'PublicKey') -> str:
        """Generiert Adresse aus Public Key"""
        if chain.lower() == "ethereum":
            return public_key.getEthereumAddress()
        elif chain.lower() == "bitcoin":
            return public_key.getBitcoinAddress()
        elif chain.lower() == "solana":
            return public_key.getSolanaAddress()
        else:
            return public_key.getEthereumAddress()  # Fallback

    async def _sign_ethereum_tx(self, tx_data: Dict[str, Any],
                               private_key: 'PrivateKey', coin_type: int) -> Dict[str, Any]:
        """Signiert Ethereum-Transaktion"""
        # Implementierung für Ethereum-Signing
        # Dies ist eine vereinfachte Version
        signature = self.wallet_core.signTransaction(
            coin_type, tx_data, private_key
        )

        return {
            "signed_tx": signature.hex(),
            "chain_id": tx_data.get("chainId", 1),
            "gas_price": tx_data.get("gasPrice"),
            "gas_limit": tx_data.get("gasLimit")
        }

    async def _sign_bitcoin_tx(self, tx_data: Dict[str, Any],
                              private_key: PrivateKey, coin_type: int) -> Dict[str, Any]:
        """Signiert Bitcoin-Transaktion"""
        # Implementierung für Bitcoin-Signing
        signature = self.wallet_core.signTransaction(
            coin_type, tx_data, private_key
        )

        return {
            "signed_tx": signature.hex(),
            "inputs": tx_data.get("inputs", []),
            "outputs": tx_data.get("outputs", [])
        }

    async def _sign_solana_tx(self, tx_data: Dict[str, Any],
                             private_key: PrivateKey, coin_type: int) -> Dict[str, Any]:
        """Signiert Solana-Transaktion"""
        # Implementierung für Solana-Signing
        signature = self.wallet_core.signTransaction(
            coin_type, tx_data, private_key
        )

        return {
            "signed_tx": signature.hex(),
            "recent_blockhash": tx_data.get("recentBlockhash"),
            "instructions": tx_data.get("instructions", [])
        }

    async def _save_wallet_data(self, wallet_data: Dict[str, Any]):
        """Speichert Wallet-Daten sicher"""
        wallet_file = self.wallet_data_dir / f"{wallet_data['id']}.json"

        # Entferne Mnemonic aus gespeicherten Daten für Sicherheit
        safe_data = wallet_data.copy()
        safe_data.pop("mnemonic", None)

        async with aiofiles.open(wallet_file, 'w') as f:
            await f.write(json.dumps(safe_data, indent=2))

    async def load_wallet_data(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        """Lädt Wallet-Daten"""
        wallet_file = self.wallet_data_dir / f"{wallet_id}.json"

        try:
            async with aiofiles.open(wallet_file, 'r') as f:
                data = json.loads(await f.read())
                return data
        except FileNotFoundError:
            return None

    async def list_wallets(self) -> List[Dict[str, Any]]:
        """Listet gespeicherte Wallets im Datenverzeichnis auf."""
        try:
            wallets: List[Dict[str, Any]] = []
            for p in self.wallet_data_dir.glob("wallet_*.json"):
                try:
                    async with aiofiles.open(p, 'r') as f:
                        data = json.loads(await f.read())
                        # minimale Felder
                        wallets.append({
                            "id": data.get("id"),
                            "chain": data.get("chain"),
                            "address": data.get("address"),
                            "public_key": data.get("public_key"),
                            "balance": data.get("balance"),
                            "created_at": data.get("created_at"),
                        })
                except Exception:
                    continue
            return wallets
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Wallets: {e}")
            return []

    async def import_wallet_from_private_key(self, chain: str, private_key_hex: str) -> Dict[str, Any]:
        """Importiert Wallet aus Private Key"""
        if not self.wallet_core:
            raise RuntimeError("Wallet Core nicht verfügbar")

        try:
            # Private Key laden
            private_key = PrivateKey(data=bytes.fromhex(private_key_hex.replace("0x", "")))
            
            # Public Key und Adresse generieren
            public_key = private_key.getPublicKeySecp256k1(False)
            address = self._get_address_from_public_key(chain, public_key)

            wallet_data = {
                "id": f"wallet_{chain}_{address[:8]}",
                "chain": chain,
                "address": address,
                "public_key": public_key.data().hex(),
                "import_type": "private_key",
                "created_at": asyncio.get_event_loop().time(),
                "balance": await self.get_balance(chain, address),
                "transactions": []
            }

            # Wallet-Daten speichern (ohne Private Key!)
            await self._save_wallet_data(wallet_data)

            return wallet_data

        except Exception as e:
            logger.error(f"Fehler beim Importieren der Wallet: {e}")
            raise

    async def analyze_wallet(self, chain: str, address: str) -> Dict[str, Any]:
        """Forensische Wallet-Analyse"""
        try:
            # Balance + Risk
            balance = await self.get_balance(chain, address)
            
            # Transaction History
            history = await self.get_wallet_history(chain, address)
            
            # Aggregiere Risk-Faktoren
            risk_factors = []
            high_risk_txs = 0
            total_in = Decimal(0)
            total_out = Decimal(0)
            
            for tx in history:
                analysis = tx.get("analysis", {})
                if analysis.get("risk_score", 0) > 0.7:
                    high_risk_txs += 1
                    risk_factors.extend(analysis.get("risk_factors", []))
                
                # Berechne In/Out
                if tx.get("to_address", "").lower() == address.lower():
                    total_in += Decimal(str(tx.get("value", 0)))
                else:
                    total_out += Decimal(str(tx.get("value", 0)))
            
            # Deduplicate Risk-Faktoren
            risk_factors = list(set(risk_factors))
            
            return {
                "address": address,
                "chain": chain,
                "balance": balance.get("balance"),
                "risk_score": balance.get("risk_score", 0),
                "total_transactions": len(history),
                "high_risk_transactions": high_risk_txs,
                "total_received": str(total_in),
                "total_sent": str(total_out),
                "risk_factors": risk_factors,
                "timestamp": asyncio.get_event_loop().time()
            }

        except Exception as e:
            logger.error(f"Fehler bei Wallet-Analyse: {e}")
            raise

    async def estimate_gas(self, chain: str, tx_type: str = "transfer", to_address: str = None) -> Dict[str, Any]:
        """Schätzt Gas-Kosten für Transaktion"""
        try:
            from app.adapters import get_adapter
            adapter = get_adapter(chain)
            if not adapter:
                raise ValueError(f"Chain {chain} nicht unterstützt")

            # Standard Gas-Limits
            gas_limits = {
                "transfer": 21000,  # ETH Transfer
                "erc20": 65000,     # ERC20 Transfer
                "contract": 200000, # Contract Interaction
            }
            
            gas_limit = gas_limits.get(tx_type, 21000)
            
            # Hole aktuelle Gas-Preise
            if chain.lower() in {"ethereum", "polygon", "bsc", "avalanche", "arbitrum", "optimism"}:
                gas_price_payload = await adapter.make_request("eth_gasPrice", [])
                gas_price_hex = gas_price_payload.get("result", "0x0")
                gas_price_wei = int(gas_price_hex, 16)
                gas_price_gwei = gas_price_wei / 1e9
                
                # Kosten berechnen
                total_cost_wei = gas_price_wei * gas_limit
                total_cost_eth = total_cost_wei / 1e18
                
                return {
                    "gas_limit": gas_limit,
                    "gas_price_gwei": round(gas_price_gwei, 2),
                    "gas_price_wei": gas_price_wei,
                    "estimated_cost_eth": round(total_cost_eth, 6),
                    "estimated_cost_usd": round(total_cost_eth * 2000, 2),  # Assuming ~$2000 ETH
                    "chain": chain
                }
            else:
                # Für andere Chains (Bitcoin, Solana)
                return {
                    "gas_limit": gas_limit,
                    "estimated_fee": "Variable",
                    "chain": chain,
                    "note": "Use chain-specific fee estimation"
                }

        except Exception as e:
            logger.error(f"Fehler bei Gas-Schätzung: {e}")
            return {
                "error": str(e),
                "gas_limit": 21000,
                "estimated_cost_eth": 0.001
            }

# Import für async file operations
try:
    import aiofiles
except ImportError:
    aiofiles = None

# Fallback für fehlende aiofiles
if not aiofiles:
    import json

    class MockAioFiles:
        @staticmethod
        async def open(file_path, mode):
            class MockFile:
                def __init__(self, path, mode):
                    self.path = path
                    self.mode = mode

                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

                async def write(self, data):
                    with open(self.path, self.mode) as f:
                        f.write(data)

                async def read(self):
                    with open(self.path, 'r') as f:
                        return f.read()

            return MockFile(file_path, mode)

    aiofiles = MockAioFiles()

# Singleton-Instance
wallet_service = WalletService()
