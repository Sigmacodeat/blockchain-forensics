import hashlib
import hmac
import os
from typing import Dict, List, Optional, Tuple
import time
import ecdsa
import base58
import requests
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from app.models.crypto_payment import CryptoWallet, CryptoPayment
from app.config import settings
import bech32


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

        # XPUB for derivation (set in env or derive from master)
        self.xpub = settings.BTC_XPUB or self._derive_xpub_from_master()

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

    def _derive_xpub_from_master(self) -> str:
        """Derive XPUB from master key (dev/test only)."""
        # For demo: derive a test XPUB
        master_seed = b"test_seed_for_demo_only_not_secure"  # NEVER use in production
        master_private = hashlib.sha256(master_seed).digest()[:32]
        sk = ecdsa.SigningKey.from_secret_exponent(int.from_bytes(master_private, 'big'), curve=ecdsa.SECP256k1)
        vk = sk.verifying_key

        # Simplified XPUB derivation (for demo)
        x = vk.pubkey.point.x()
        y = vk.pubkey.point.y()
        public_key = b'\x02' + x.to_bytes(32, 'big') if y % 2 == 0 else b'\x03' + x.to_bytes(32, 'big')
        # Return mock XPUB (in reality, use BIP32 derivation)
        return "xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8"  # Test XPUB

    def derive_address(self, index: int) -> Tuple[str, str]:
        """Derive BTC address from XPUB at given index (BIP44-like)."""
        # Simplified derivation (use proper BIP32 in production)
        xpub_bytes = base58.b58decode_check(self.xpub)[4:]  # Remove version
        derived_priv = hmac.new(xpub_bytes[:32], index.to_bytes(4, 'big'), hashlib.sha512).digest()
        priv_key = derived_priv[:32]
        sk = ecdsa.SigningKey.from_secret_exponent(int.from_bytes(priv_key, 'big'), curve=ecdsa.SECP256k1)
        vk = sk.verifying_key

        # P2PKH for compatibility
        x = vk.pubkey.point.x()
        y = vk.pubkey.point.y()
        compressed_pub = b'\x02' + x.to_bytes(32, 'big') if y % 2 == 0 else b'\x03' + x.to_bytes(32, 'big')

        # SHA256 and RIPEMD160
        sha = hashlib.sha256(compressed_pub).digest()
        rip = hashlib.new('ripemd160', sha).digest()

        # Version byte + checksum
        version_rip = b'\x00' + rip
        checksum = hashlib.sha256(hashlib.sha256(version_rip).digest()).digest()[:4]
        address = base58.b58encode(version_rip + checksum).decode()

        return address, self.cipher.encrypt(priv_key).decode()

    def derive_bech32_address(self, index: int, use_taproot: bool = False) -> Tuple[str, str]:
        """Derive modern bech32 address (BIP84 P2WPKH or BIP86 P2TR Taproot)."""
        # Simplified derivation (use proper BIP32/BIP84/BIP86 in production)
        xpub_bytes = base58.b58decode_check(self.xpub)[4:]  # Remove version
        derived_priv = hmac.new(xpub_bytes[:32], index.to_bytes(4, 'big'), hashlib.sha512).digest()
        priv_key = derived_priv[:32]
        sk = ecdsa.SigningKey.from_secret_exponent(int.from_bytes(priv_key, 'big'), curve=ecdsa.SECP256k1)
        vk = sk.verifying_key

        # Compressed public key
        x = vk.pubkey.point.x()
        y = vk.pubkey.point.y()
        compressed_pub = b'\x02' + x.to_bytes(32, 'big') if y % 2 == 0 else b'\x03' + x.to_bytes(32, 'big')

        if use_taproot:
            # BIP86 Taproot (P2TR) - simplified
            # In production, use proper schnorr signatures and tweaked keys
            hrp = "bc"  # mainnet
            version = 1  # P2TR version
            # Simplified: just use compressed pubkey hash
            pubkey_hash = hashlib.sha256(compressed_pub).digest()
        else:
            # BIP84 P2WPKH
            hrp = "bc"  # mainnet
            version = 0  # witness version

            # P2WPKH: HASH160(compressed_pubkey)
            sha = hashlib.sha256(compressed_pub).digest()
            rip = hashlib.new('ripemd160', sha).digest()
            pubkey_hash = rip

        # Create bech32 address
        data = [version] + [b for b in pubkey_hash]
        encoded = bech32.encode(hrp, data)
        if not encoded:
            raise ValueError("Bech32 encoding failed")

        return encoded, self.cipher.encrypt(priv_key).decode()

    def generate_invoice_address(self, order_id: str, plan_name: str, expected_btc: float, use_bech32: bool = True) -> Dict[str, str]:
        """Generate unique address for invoice (modern bech32 by default)."""
        index = int(hashlib.sha256(f"{order_id}:{plan_name}".encode()).hexdigest(), 16) % 2**31

        if use_bech32:
            address, encrypted_priv = self.derive_bech32_address(index, use_taproot=False)  # P2WPKH
        else:
            address, encrypted_priv = self.derive_address(index)  # Legacy P2PKH

        return {
            "address": address,
            "encrypted_private_key": encrypted_priv,
            "index": str(index),
            "order_id": order_id,
            "plan_name": plan_name,
            "expected_amount_btc": str(expected_btc),
            "address_type": "bech32_p2wpkh" if use_bech32 else "p2pkh"
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

    def get_total_received(self, address: str) -> float:
        """Return total received (lifetime) for an address using funded_txo_sum.
        Includes mempool to capture incoming unconfirmed funds.
        """
        base = settings.BTC_ESPLORA_BASE_URL.rstrip("/")
        try:
            r = requests.get(f"{base}/address/{address}", timeout=15)
            if r.status_code == 200:
                data = r.json()
                chain = data.get("chain_stats", {})
                mempool = data.get("mempool_stats", {})
                funded = int(chain.get("funded_txo_sum", 0)) + int(mempool.get("funded_txo_sum", 0))
                return funded / 100_000_000
        except Exception as e:
            print(f"BTC total received fetch failed: {e}")
        return 0.0

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
