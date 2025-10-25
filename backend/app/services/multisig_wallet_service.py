"""
Multi-Signature Wallet Service

Implementiert Multi-Sig Wallets für erweiterte Sicherheit und Compliance.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path

# Kryptografische Bibliotheken für Multi-Sig
try:
    import ecdsa
    from ecdsa import SigningKey, VerifyingKey
    import hashlib
    import base58
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    logging.warning("ECDSA nicht verfügbar - Multi-Sig Features werden deaktiviert")

from app.services.wallet_service import wallet_service

logger = logging.getLogger(__name__)

class MultiSigWallet:
    """Multi-Signature Wallet Implementierung"""

    def __init__(self, wallet_id: str, required_signatures: int = 2):
        self.wallet_id = wallet_id
        self.required_signatures = required_signatures
        self.signers: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.completed_transactions: List[Dict[str, Any]] = []
        self.created_at = datetime.utcnow()

    def add_signer(self, public_key: str, name: str, role: str = "signer") -> bool:
        """Fügt einen Unterzeichner hinzu"""
        if len(self.signers) >= 10:  # Max 10 Unterzeichner
            return False

        # Prüfen ob Public Key bereits vorhanden
        for signer in self.signers:
            if signer["public_key"] == public_key:
                return False

        self.signers.append({
            "public_key": public_key,
            "name": name,
            "role": role,
            "added_at": datetime.utcnow().isoformat()
        })

        return True

    def remove_signer(self, public_key: str) -> bool:
        """Entfernt einen Unterzeichner"""
        for i, signer in enumerate(self.signers):
            if signer["public_key"] == public_key:
                self.signers.pop(i)
                return True
        return False

    async def create_transaction(
        self,
        to_address: str,
        amount: str,
        chain: str,
        description: str = "",
        expires_in: int = 86400  # 24 Stunden
    ) -> str:
        """Erstellt eine neue Multi-Sig Transaktion"""

        tx_id = f"multisig_tx_{self.wallet_id}_{int(datetime.utcnow().timestamp())}"

        transaction = {
            "tx_id": tx_id,
            "to_address": to_address,
            "amount": amount,
            "chain": chain,
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            "status": "pending",
            "signatures": [],
            "required_signatures": self.required_signatures,
            "creator": "system"  # Würde aus Auth kommen
        }

        self.pending_transactions.append(transaction)

        logger.info(f"Multi-Sig Transaktion {tx_id} erstellt für Wallet {self.wallet_id}")
        return tx_id

    async def sign_transaction(
        self,
        tx_id: str,
        signer_public_key: str,
        signature: str
    ) -> Dict[str, Any]:
        """Unterzeichnet eine Transaktion"""

        # Transaktion finden
        transaction = None
        for tx in self.pending_transactions:
            if tx["tx_id"] == tx_id:
                transaction = tx
                break

        if not transaction:
            raise ValueError(f"Transaktion {tx_id} nicht gefunden")

        # Prüfen ob abgelaufen
        expires_at = datetime.fromisoformat(transaction["expires_at"])
        if datetime.utcnow() > expires_at:
            transaction["status"] = "expired"
            raise ValueError("Transaktion ist abgelaufen")

        # Prüfen ob bereits unterzeichnet
        for sig in transaction["signatures"]:
            if sig["signer_public_key"] == signer_public_key:
                raise ValueError("Bereits unterzeichnet")

        # Signatur hinzufügen
        transaction["signatures"].append({
            "signer_public_key": signer_public_key,
            "signature": signature,
            "signed_at": datetime.utcnow().isoformat()
        })

        # Prüfen ob genug Signaturen vorhanden
        if len(transaction["signatures"]) >= self.required_signatures:
            await self._execute_transaction(transaction)

        return {
            "tx_id": tx_id,
            "status": transaction["status"],
            "signatures_count": len(transaction["signatures"]),
            "required_signatures": self.required_signatures
        }

    async def _execute_transaction(self, transaction: Dict[str, Any]):
        """Führt eine vollständig unterzeichnete Transaktion aus"""
        try:
            # Transaktion ausführen (würde echte Blockchain-Interaktion verwenden)
            # Für Demo: Simuliere erfolgreiche Ausführung
            transaction["status"] = "executed"
            transaction["executed_at"] = datetime.utcnow().isoformat()
            transaction["tx_hash"] = f"0x{hash(transaction['tx_id']) & 0xFFFFFFFFFFFFFFFF:016x}"

            # Von pending zu completed verschieben
            self.pending_transactions.remove(transaction)
            self.completed_transactions.append(transaction)

            logger.info(f"Multi-Sig Transaktion {transaction['tx_id']} erfolgreich ausgeführt")

        except Exception as e:
            logger.error(f"Fehler bei Ausführung der Transaktion {transaction['tx_id']}: {e}")
            transaction["status"] = "failed"
            transaction["error"] = str(e)

    def get_pending_transactions(self) -> List[Dict[str, Any]]:
        """Holt alle ausstehenden Transaktionen"""
        # Abgelaufene Transaktionen entfernen
        current_time = datetime.utcnow()
        self.pending_transactions = [
            tx for tx in self.pending_transactions
            if datetime.fromisoformat(tx["expires_at"]) > current_time
        ]

        return self.pending_transactions

    def get_transaction_status(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """Holt den Status einer spezifischen Transaktion"""
        # In pending suchen
        for tx in self.pending_transactions:
            if tx["tx_id"] == tx_id:
                return tx

        # In completed suchen
        for tx in self.completed_transactions:
            if tx["tx_id"] == tx_id:
                return tx

        return None

class MultiSigWalletManager:
    """Manager für mehrere Multi-Signature Wallets"""

    def __init__(self):
        self.wallets: Dict[str, MultiSigWallet] = {}
        self.wallet_data_dir = Path("data/multisig_wallets")
        self.wallet_data_dir.mkdir(parents=True, exist_ok=True)

    def create_wallet(
        self,
        wallet_id: str,
        required_signatures: int = 2,
        name: str = ""
    ) -> MultiSigWallet:
        """Erstellt eine neue Multi-Sig Wallet"""
        if wallet_id in self.wallets:
            raise ValueError(f"Multi-Sig Wallet {wallet_id} existiert bereits")

        wallet = MultiSigWallet(wallet_id, required_signatures)
        self.wallets[wallet_id] = wallet

        # Wallet-Daten speichern
        self._save_wallet(wallet)

        logger.info(f"Multi-Sig Wallet {wallet_id} erstellt mit {required_signatures} erforderlichen Signaturen")
        return wallet

    def get_wallet(self, wallet_id: str) -> Optional[MultiSigWallet]:
        """Holt eine Multi-Sig Wallet"""
        if wallet_id not in self.wallets:
            # Versuche aus Datei zu laden
            wallet = self._load_wallet(wallet_id)
            if wallet:
                self.wallets[wallet_id] = wallet

        return self.wallets.get(wallet_id)

    def list_wallets(self) -> List[Dict[str, Any]]:
        """Listet alle Multi-Sig Wallets auf"""
        wallets = []
        for wallet_id, wallet in self.wallets.items():
            wallets.append({
                "wallet_id": wallet_id,
                "required_signatures": wallet.required_signatures,
                "signer_count": len(wallet.signers),
                "pending_txs": len(wallet.get_pending_transactions()),
                "completed_txs": len(wallet.completed_transactions),
                "created_at": wallet.created_at.isoformat()
            })

        return wallets

    def _save_wallet(self, wallet: MultiSigWallet):
        """Speichert Wallet-Daten"""
        filepath = self.wallet_data_dir / f"{wallet.wallet_id}.json"

        data = {
            "wallet_id": wallet.wallet_id,
            "required_signatures": wallet.required_signatures,
            "signers": wallet.signers,
            "pending_transactions": wallet.pending_transactions,
            "completed_transactions": wallet.completed_transactions,
            "created_at": wallet.created_at.isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_wallet(self, wallet_id: str) -> Optional[MultiSigWallet]:
        """Lädt Wallet-Daten aus Datei"""
        filepath = self.wallet_data_dir / f"{wallet_id}.json"

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            wallet = MultiSigWallet(data["wallet_id"], data["required_signatures"])
            wallet.signers = data["signers"]
            wallet.pending_transactions = data["pending_transactions"]
            wallet.completed_transactions = data["completed_transactions"]
            wallet.created_at = datetime.fromisoformat(data["created_at"])

            return wallet

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Fehler beim Laden der Wallet {wallet_id}: {e}")
            return None

# Singleton-Instance
multisig_manager = MultiSigWalletManager()
