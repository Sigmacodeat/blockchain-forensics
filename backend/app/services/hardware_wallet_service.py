"""
Hardware Wallet Integration für Blockchain-Forensik-Plattform

Unterstützt Ledger und Trezor für sichere Schlüsselverwaltung.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json

# Hardware Wallet Libraries
try:
    from ledgerblue.Dongle import Dongle
    from trezorlib.client import TrezorClient
    from trezorlib.transport import Transport
    _HARDWARE_WALLETS_AVAILABLE = True
except ImportError:
    _HARDWARE_WALLETS_AVAILABLE = False
    logging.warning("Hardware Wallet Libraries nicht verfügbar")

from app.services.wallet_service import wallet_service

logger = logging.getLogger(__name__)

class HardwareWalletType(Enum):
    LEDGER = "ledger"
    TREZOR = "trezor"

class HardwareWalletManager:
    """Manager für Hardware-Wallet-Integrationen"""

    def __init__(self):
        self.ledger_devices = {}
        self.trezor_devices = {}

    async def detect_devices(self) -> List[Dict[str, Any]]:
        """Erkennt verfügbare Hardware-Wallets"""
        devices = []

        if not _HARDWARE_WALLETS_AVAILABLE:
            logger.warning("Hardware Wallet Detection nicht verfügbar")
            return devices

        try:
            # Ledger-Geräte erkennen
            ledger_devices = await self._detect_ledger_devices()
            devices.extend(ledger_devices)

            # Trezor-Geräte erkennen
            trezor_devices = await self._detect_trezor_devices()
            devices.extend(trezor_devices)

        except Exception as e:
            logger.error(f"Fehler bei Hardware-Wallet-Erkennung: {e}")

        return devices

    async def _detect_ledger_devices(self) -> List[Dict[str, Any]]:
        """Erkennt Ledger-Geräte"""
        devices = []

        try:
            # Ledger über HID suchen
            dongle = Dongle()

            # Geräte-Info abrufen
            device_info = {
                "type": HardwareWalletType.LEDGER.value,
                "model": "Ledger Nano S/X",
                "connected": True,
                "firmware_version": await self._get_ledger_firmware(dongle),
                "supported_chains": self._get_ledger_supported_chains()
            }

            devices.append(device_info)
            self.ledger_devices[device_info["model"]] = dongle

        except Exception as e:
            logger.debug(f"Kein Ledger-Gerät gefunden: {e}")
        finally:
            try:
                if 'dongle' in locals():
                    dongle.close()
            except:
                pass

        return devices

    async def _detect_trezor_devices(self) -> List[Dict[str, Any]]:
        """Erkennt Trezor-Geräte"""
        devices = []

        try:
            # Trezor über verschiedene Transportmethoden suchen
            transports = [
                Transport.HID,
                Transport.BRIDGE,
                Transport.WEBUSB
            ]

            for transport_type in transports:
                try:
                    transport = Transport(transport_type)
                    client = TrezorClient(transport)

                    features = client.get_features()

                    device_info = {
                        "type": HardwareWalletType.TREZOR.value,
                        "model": features.model,
                        "connected": True,
                        "firmware_version": features.firmware_version,
                        "supported_chains": self._get_trezor_supported_chains()
                    }

                    devices.append(device_info)
                    self.trezor_devices[features.model] = client

                    client.close()
                    break  # Erstes gefundenes Gerät verwenden

                except Exception as e:
                    logger.debug(f"Trezor {transport_type} nicht gefunden: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Fehler bei Trezor-Erkennung: {e}")

        return devices

    async def sign_with_hardware_wallet(
        self,
        wallet_type: HardwareWalletType,
        chain: str,
        tx_data: Dict[str, Any],
        derivation_path: str = "m/44'/60'/0'/0/0"
    ) -> Dict[str, Any]:
        """Signiert eine Transaktion mit Hardware-Wallet"""

        if wallet_type == HardwareWalletType.LEDGER:
            return await self._sign_with_ledger(chain, tx_data, derivation_path)
        elif wallet_type == HardwareWalletType.TREZOR:
            return await self._sign_with_trezor(chain, tx_data, derivation_path)
        else:
            raise ValueError(f"Nicht unterstützter Wallet-Typ: {wallet_type}")

    async def _sign_with_ledger(
        self,
        chain: str,
        tx_data: Dict[str, Any],
        derivation_path: str
    ) -> Dict[str, Any]:
        """Signiert mit Ledger"""

        if not self.ledger_devices:
            raise RuntimeError("Kein Ledger-Gerät verbunden")

        dongle = list(self.ledger_devices.values())[0]

        try:
            # Chain-spezifisches Signing
            if chain.lower() == "ethereum":
                return await self._sign_ethereum_ledger(dongle, tx_data, derivation_path)
            elif chain.lower() == "bitcoin":
                return await self._sign_bitcoin_ledger(dongle, tx_data, derivation_path)
            else:
                raise ValueError(f"Ledger-Signing für {chain} nicht implementiert")

        except Exception as e:
            logger.error(f"Ledger-Signing fehlgeschlagen: {e}")
            raise
        finally:
            try:
                dongle.close()
            except:
                pass

    async def _sign_with_trezor(
        self,
        chain: str,
        tx_data: Dict[str, Any],
        derivation_path: str
    ) -> Dict[str, Any]:
        """Signiert mit Trezor"""

        if not self.trezor_devices:
            raise RuntimeError("Kein Trezor-Gerät verbunden")

        client = list(self.trezor_devices.values())[0]

        try:
            # Chain-spezifisches Signing
            if chain.lower() == "ethereum":
                return await self._sign_ethereum_trezor(client, tx_data, derivation_path)
            elif chain.lower() == "bitcoin":
                return await self._sign_bitcoin_trezor(client, tx_data, derivation_path)
            else:
                raise ValueError(f"Trezor-Signing für {chain} nicht implementiert")

        except Exception as e:
            logger.error(f"Trezor-Signing fehlgeschlagen: {e}")
            raise
        finally:
            try:
                client.close()
            except:
                pass

    async def _sign_ethereum_ledger(
        self,
        dongle: Dongle,
        tx_data: Dict[str, Any],
        derivation_path: str
    ) -> Dict[str, Any]:
        """Ethereum-Signing mit Ledger"""

        # BIP44 Derivation Path für Ethereum
        path_bytes = self._parse_derivation_path(derivation_path)

        # Öffentliche Schlüssel abrufen
        public_key = dongle.get_public_key(path_bytes)

        # Transaktion vorbereiten und signieren
        # Dies ist eine vereinfachte Version - echte Implementierung würde
        # die Ethereum-App auf dem Ledger verwenden
        tx_hash = self._hash_ethereum_transaction(tx_data)

        # Signatur mit Ledger erstellen
        signature = dongle.sign_tx(path_bytes, tx_hash)

        return {
            "signature": signature.hex(),
            "public_key": public_key.hex(),
            "tx_hash": tx_hash.hex(),
            "chain": "ethereum"
        }

    async def _sign_bitcoin_ledger(
        self,
        dongle: Dongle,
        tx_data: Dict[str, Any],
        derivation_path: str
    ) -> Dict[str, Any]:
        """Bitcoin-Signing mit Ledger"""

        path_bytes = self._parse_derivation_path(derivation_path)

        # Bitcoin-App auf Ledger verwenden
        public_key = dongle.get_public_key(path_bytes)

        # Transaktion vorbereiten
        tx_hash = self._hash_bitcoin_transaction(tx_data)

        signature = dongle.sign_tx(path_bytes, tx_hash)

        return {
            "signature": signature.hex(),
            "public_key": public_key.hex(),
            "tx_hash": tx_hash.hex(),
            "chain": "bitcoin"
        }

    async def _sign_ethereum_trezor(
        self,
        client: TrezorClient,
        tx_data: Dict[str, Any],
        derivation_path: str
    ) -> Dict[str, Any]:
        """Ethereum-Signing mit Trezor"""

        # Trezor Ethereum-Signing
        from trezorlib import ethereum

        tx_hash = self._hash_ethereum_transaction(tx_data)

        signature = ethereum.sign_tx(
            client,
            derivation_path,
            tx_data.get("nonce", 0),
            tx_data.get("gas_price", 0),
            tx_data.get("gas_limit", 21000),
            tx_data.get("to", ""),
            tx_data.get("value", 0),
            tx_data.get("data", b"")
        )

        return {
            "signature": signature.signature.hex(),
            "public_key": signature.address,  # Trezor gibt Adresse zurück
            "tx_hash": tx_hash.hex(),
            "chain": "ethereum"
        }

    async def _sign_bitcoin_trezor(
        self,
        client: TrezorClient,
        tx_data: Dict[str, Any],
        derivation_path: str
    ) -> Dict[str, Any]:
        """Bitcoin-Signing mit Trezor"""

        from trezorlib import bitcoin

        # Bitcoin-Signing implementieren
        tx_hash = self._hash_bitcoin_transaction(tx_data)

        signature = bitcoin.sign_tx(
            client,
            derivation_path,
            tx_data.get("inputs", []),
            tx_data.get("outputs", [])
        )

        return {
            "signature": signature.hex(),
            "tx_hash": tx_hash.hex(),
            "chain": "bitcoin"
        }

    def _parse_derivation_path(self, path: str) -> bytes:
        """Parst Derivation Path in Bytes"""
        # Vereinfachte Implementierung
        # BIP44: m / purpose' / coin_type' / account' / change / address_index
        parts = path.replace("m/", "").split("/")
        return bytes([int(p.rstrip("'")) for p in parts])

    def _hash_ethereum_transaction(self, tx_data: Dict[str, Any]) -> bytes:
        """Hash einer Ethereum-Transaktion"""
        # Vereinfachte Version - echte Implementierung würde
        # RLP-Encoding und Keccak-Hashing verwenden
        import hashlib

        tx_str = json.dumps(tx_data, sort_keys=True)
        return hashlib.keccak(tx_str.encode()).digest()

    def _hash_bitcoin_transaction(self, tx_data: Dict[str, Any]) -> bytes:
        """Hash einer Bitcoin-Transaktion"""
        # Vereinfachte Version
        import hashlib

        tx_str = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_str.encode()).digest()

    def _get_ledger_firmware(self, dongle: Dongle) -> str:
        """Holt Ledger Firmware-Version"""
        try:
            # Firmware-Version abrufen
            return "2.1.0"  # Platzhalter
        except:
            return "unknown"

    def _get_ledger_supported_chains(self) -> List[str]:
        """Gibt Ledger-unterstützte Chains zurück"""
        return [
            "ethereum", "bitcoin", "litecoin", "dogecoin",
            "ethereum_classic", "dash", "zcash"
        ]

    def _get_trezor_supported_chains(self) -> List[str]:
        """Gibt Trezor-unterstützte Chains zurück"""
        return [
            "ethereum", "bitcoin", "litecoin", "dash",
            "zcash", "bitcoin_cash", "cardano"
        ]

    async def get_address_from_hardware_wallet(
        self,
        wallet_type: HardwareWalletType,
        chain: str,
        derivation_path: str = "m/44'/60'/0'/0/0"
    ) -> str:
        """Holt Adresse von Hardware-Wallet ohne Signing"""

        if wallet_type == HardwareWalletType.LEDGER:
            return await self._get_ledger_address(chain, derivation_path)
        elif wallet_type == HardwareWalletType.TREZOR:
            return await self._get_trezor_address(chain, derivation_path)
        else:
            raise ValueError(f"Nicht unterstützter Wallet-Typ: {wallet_type}")

    async def _get_ledger_address(self, chain: str, derivation_path: str) -> str:
        """Holt Adresse von Ledger"""
        if not self.ledger_devices:
            raise RuntimeError("Kein Ledger-Gerät verbunden")

        dongle = list(self.ledger_devices.values())[0]

        try:
            path_bytes = self._parse_derivation_path(derivation_path)
            public_key = dongle.get_public_key(path_bytes)

            # Adresse aus Public Key generieren
            if chain.lower() == "ethereum":
                return self._public_key_to_ethereum_address(public_key)
            elif chain.lower() == "bitcoin":
                return self._public_key_to_bitcoin_address(public_key)
            else:
                return self._public_key_to_ethereum_address(public_key)

        finally:
            dongle.close()

    async def _get_trezor_address(self, chain: str, derivation_path: str) -> str:
        """Holt Adresse von Trezor"""
        if not self.trezor_devices:
            raise RuntimeError("Kein Trezor-Gerät verbunden")

        client = list(self.trezor_devices.values())[0]

        try:
            from trezorlib import ethereum

            address = ethereum.get_address(client, derivation_path)
            return address

        finally:
            client.close()

    def _public_key_to_ethereum_address(self, public_key: bytes) -> str:
        """Konvertiert Public Key zu Ethereum-Adresse"""
        import hashlib

        # Keccak-256 Hash des Public Keys (ohne 0x04 Prefix)
        if public_key.startswith(b'\x04'):
            public_key = public_key[1:]

        keccak_hash = hashlib.keccak(public_key).digest()
        # Letzte 20 Bytes als Adresse
        address = keccak_hash[-20:]

        return "0x" + address.hex()

    def _public_key_to_bitcoin_address(self, public_key: bytes) -> str:
        """Konvertiert Public Key zu Bitcoin-Adresse"""
        import hashlib
        import base58

        # RIPEMD-160(SHA-256(Public Key))
        if public_key.startswith(b'\x04'):
            public_key = public_key[1:]

        sha256_hash = hashlib.sha256(public_key).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        hash160 = ripemd160.digest()

        # Base58Check Encoding
        return base58.b58encode_check(b'\x00' + hash160).decode()

# Singleton-Instance
hardware_wallet_manager = HardwareWalletManager()
