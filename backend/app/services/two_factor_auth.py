"""
Zwei-Faktor-Authentifizierung (2FA) für Blockchain-Forensik-Anwendung

Implementiert TOTP (Time-based One-Time Password) für zusätzliche Sicherheit.
"""

import asyncio
import logging
import secrets
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import base64
import hmac
import hashlib
import struct
import time

# 2FA-Bibliotheken (optional)
try:
    import pyotp
    import qrcode
    from cryptography.fernet import Fernet
    _TWO_FA_AVAILABLE = True
except ImportError:
    _TWO_FA_AVAILABLE = False
    logging.warning("2FA-Bibliotheken nicht verfügbar - 2FA wird deaktiviert")

from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

class TwoFactorAuth:
    """2FA-Implementierung mit TOTP"""

    def __init__(self, secret_key: Optional[str] = None):
        # Initialize depending on library availability
        if _TWO_FA_AVAILABLE:
            self.secret_key = secret_key or Fernet.generate_key()
            self.fernet = Fernet(self.secret_key)
        else:
            # Fallback: generate a random secret without Fernet
            self.secret_key = secret_key or secrets.token_urlsafe(32)
            self.fernet = None

        if _TWO_FA_AVAILABLE:
            # Standard-TOTP-Konfiguration
            self.totp_digits = 6
            self.totp_interval = 30  # 30 Sekunden

    def generate_secret(self) -> str:
        """Generiert einen neuen 2FA-Secret"""
        if not _TWO_FA_AVAILABLE:
            raise RuntimeError("2FA-Bibliotheken nicht verfügbar")

        # 32 Bytes random secret generieren
        secret_bytes = secrets.token_bytes(32)
        secret_b32 = base64.b32encode(secret_bytes).decode('utf-8')

        return secret_b32

    def generate_qr_code(self, secret: str, account_name: str, issuer_name: str = "BlockchainForensik") -> bytes:
        """Generiert QR-Code für 2FA-Setup"""
        if not _TWO_FA_AVAILABLE:
            raise RuntimeError("2FA-Bibliotheken nicht verfügbar")

        # TOTP-URI erstellen
        totp_uri = f"otpauth://totp/{issuer_name}:{account_name}?secret={secret}&issuer={issuer_name}&digits={self.totp_digits}&period={self.totp_interval}"

        # QR-Code generieren
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # QR-Code als Bytes zurückgeben (PNG-Format)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return img_bytes.getvalue()

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verifiziert einen TOTP-Token"""
        if not _TWO_FA_AVAILABLE:
            return False

        try:
            totp = pyotp.TOTP(secret, digits=self.totp_digits, interval=self.totp_interval)
            return totp.verify(token)
        except Exception as e:
            logger.error(f"2FA-Verifikation fehlgeschlagen: {e}")
            return False

    def encrypt_secret(self, secret: str) -> str:
        """Verschlüsselt einen 2FA-Secret"""
        if not _TWO_FA_AVAILABLE or not self.fernet:
            return secret

        return self.fernet.encrypt(secret.encode()).decode()

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Entschlüsselt einen 2FA-Secret"""
        if not _TWO_FA_AVAILABLE or not self.fernet:
            return encrypted_secret

        try:
            return self.fernet.decrypt(encrypted_secret.encode()).decode()
        except Exception as e:
            logger.error(f"2FA-Secret-Entschlüsselung fehlgeschlagen: {e}")
            return ""

class TwoFactorAuthManager:
    """Manager für 2FA-Operationen"""

    def __init__(self):
        self.two_fa = TwoFactorAuth()
        self.user_secrets: Dict[str, str] = {}  # user_id -> encrypted_secret
        self.backup_codes: Dict[str, List[str]] = {}  # user_id -> backup_codes

    def setup_2fa_for_user(self, user_id: str, account_name: str) -> Dict[str, Any]:
        """Richtet 2FA für einen Benutzer ein"""
        if not _TWO_FA_AVAILABLE:
            raise RuntimeError("2FA nicht verfügbar")

        # Secret generieren
        secret = self.two_fa.generate_secret()

        # Backup-Codes generieren (10 Codes)
        backup_codes = []
        for _ in range(10):
            backup_codes.append(secrets.token_hex(4).upper())

        # Daten speichern
        encrypted_secret = self.two_fa.encrypt_secret(secret)
        self.user_secrets[user_id] = encrypted_secret
        self.backup_codes[user_id] = backup_codes

        # QR-Code generieren
        qr_code = self.two_fa.generate_qr_code(secret, account_name)

        return {
            "secret": secret,  # Nur für QR-Code-Generierung
            "qr_code": base64.b64encode(qr_code).decode(),
            "backup_codes": backup_codes,
            "setup_complete": False
        }

    def verify_2fa_setup(self, user_id: str, token: str) -> bool:
        """Verifiziert die 2FA-Einrichtung"""
        if user_id not in self.user_secrets:
            return False

        encrypted_secret = self.user_secrets[user_id]
        secret = self.two_fa.decrypt_secret(encrypted_secret)

        return self.two_fa.verify_totp(secret, token)

    def verify_2fa_login(self, user_id: str, token: str) -> bool:
        """Verifiziert 2FA-Token für Login"""
        if user_id not in self.user_secrets:
            return False

        encrypted_secret = self.user_secrets[user_id]
        secret = self.two_fa.decrypt_secret(encrypted_secret)

        return self.two_fa.verify_totp(secret, token)

    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verifiziert einen Backup-Code"""
        if user_id not in self.backup_codes:
            return False

        # Backup-Code entfernen nach Verwendung (Einmal-Verwendung)
        codes = self.backup_codes[user_id]
        if code in codes:
            codes.remove(code)
            return True

        return False

    def disable_2fa_for_user(self, user_id: str) -> bool:
        """Deaktiviert 2FA für einen Benutzer"""
        if user_id in self.user_secrets:
            del self.user_secrets[user_id]
        if user_id in self.backup_codes:
            del self.backup_codes[user_id]
        return True

    def get_2fa_status(self, user_id: str) -> Dict[str, Any]:
        """Holt 2FA-Status für einen Benutzer"""
        has_2fa = user_id in self.user_secrets
        remaining_backup_codes = len(self.backup_codes.get(user_id, []))

        return {
            "enabled": has_2fa,
            "backup_codes_remaining": remaining_backup_codes if has_2fa else 0,
            "setup_required": not has_2fa
        }

# Import für async file operations (für QR-Code)
try:
    import aiofiles
    import io
except ImportError:
    aiofiles = None

# Fallback für fehlende aiofiles
if not aiofiles:
    import io

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
                    with open(self.path, 'rb') as f:
                        return f.read()

            return MockFile(file_path, mode)

    aiofiles = MockAioFiles()

# Singleton-Instance
two_fa_manager = TwoFactorAuthManager()
