import hashlib
import os
from typing import Dict, List, Optional
import time
import ecdsa
import base58
import requests
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from app.models.crypto_payment import CryptoWallet, CryptoPayment
from app.config import settings


class BTCWalletService:
    def __init__(self):
        # Encryption key from env (generate and store securely!)
        if settings.WALLET_ENCRYPTION_KEY:
            self.encryption_key = settings.WALLET_ENCRYPTION_KEY.encode() if isinstance(settings.WALLET_ENCRYPTION_KEY, str) else settings.WALLET_ENCRYPTION_KEY
        else:
            # Only allow auto-generate in explicit development/test modes
            env = (settings.ENVIRONMENT or "development").lower()
            if env not in ("development", "dev", "test", "testing"):
                raise RuntimeError("WALLET_ENCRYPTION_KEY must be set in production environments")
            self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)

    def generate_address(self) -> Dict[str, str]:
        """Generate a new BTC address and private key."""
        private_key = os.urandom(32)
        priv_hex = private_key.hex()

        # Derive public key
        sk = ecdsa.SigningKey.from_secret_exponent(int.from_bytes(private_key, 'big'), curve=ecdsa.SECP256k1)
        vk = sk.verifying_key

        # Compressed public key
        x = vk.pubkey.point.x()
        y = vk.pubkey.point.y()
        public_key = b'\x02' + x.to_bytes(32, 'big') if y % 2 == 0 else b'\x03' + x.to_bytes(32, 'big')

        # SHA256 and RIPEMD160
        sha = hashlib.sha256(public_key).digest()
        rip = hashlib.new('ripemd160', sha).digest()

        # Version byte + checksum
        version_rip = b'\x00' + rip
        checksum = hashlib.sha256(hashlib.sha256(version_rip).digest()).digest()[:4]
        address = base58.b58encode(version_rip + checksum).decode()

        return {
            'address': address,
            'private_key_encrypted': self.cipher.encrypt(priv_hex.encode()).decode()
        }

    def get_balance(self, address: str) -> float:
        """Get BTC balance using Esplora-compatible API."""
        base = settings.BTC_ESPLORA_BASE_URL.rstrip("/")
        try:
            r = requests.get(f"{base}/address/{address}", timeout=15)
            if r.status_code == 200:
                data = r.json()
                chain = data.get("chain_stats", {})
                mempool = data.get("mempool_stats", {})
                funded = int(chain.get("funded_txo_sum", 0)) + int(mempool.get("funded_txo_sum", 0))
                spent = int(chain.get("spent_txo_sum", 0)) + int(mempool.get("spent_txo_sum", 0))
                return (funded - spent) / 100_000_000
        except Exception as e:
            print(f"BTC balance check failed: {e}")
        return 0.0

    def get_transactions(self, address: str) -> List[Dict]:
        """Get recent transactions (Esplora). Returns simplified tx list with net value for address."""
        base = settings.BTC_ESPLORA_BASE_URL.rstrip("/")
        try:
            r = requests.get(f"{base}/address/{address}/txs", timeout=20)
            if r.status_code != 200:
                return []
            txs = r.json()
            simplified: List[Dict] = []
            for tx in txs[:10]:
                # Compute net value for this address: outputs_to_addr - inputs_from_addr
                vout = tx.get("vout", [])
                vin = tx.get("vin", [])
                out_sats = sum(int(o.get("value", 0)) for o in vout if o.get("scriptpubkey_address") == address)
                in_sats = 0
                for i in vin:
                    prev = i.get("prevout") or {}
                    if prev.get("scriptpubkey_address") == address:
                        in_sats += int(prev.get("value", 0))
                net_btc = (out_sats - in_sats) / 100_000_000
                status = tx.get("status", {})
                confirmed = bool(status.get("confirmed"))
                block_time = int(status.get("block_time") or 0)
                if not block_time:
                    block_time = int(time.time())
                simplified.append({
                    "hash": tx.get("txid"),
                    "value": net_btc,
                    "confirmations": 1 if confirmed else 0,
                    "time": block_time,
                })
            return simplified
        except Exception as e:
            print(f"BTC transactions fetch failed: {e}")
            return []

    def decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt private key."""
        return self.cipher.decrypt(encrypted_key.encode()).decode()

    def store_wallet(self, db: Session, user_id: str, address: str, private_key_encrypted: str) -> CryptoWallet:
        """Store wallet in database."""
        wallet = CryptoWallet(
            user_id=user_id,
            currency='BTC',
            address=address,
            private_key_encrypted=private_key_encrypted,
            balance=0.0
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        return wallet

    def get_wallet(self, db: Session, user_id: str) -> Optional[CryptoWallet]:
        """Get user's BTC wallet."""
        return db.query(CryptoWallet).filter(
            CryptoWallet.user_id == user_id,
            CryptoWallet.currency == 'BTC'
        ).first()

    def update_balance(self, db: Session, wallet: CryptoWallet):
        """Update wallet balance."""
        wallet.balance = self.get_balance(wallet.address)
        db.commit()


# Global instance
btc_wallet_service = BTCWalletService()
