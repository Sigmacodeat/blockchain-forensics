"""
Security & Compliance für Wallet Scanner
- Memory-Wipe (sensible Daten)
- Secret-Detection (DLP)
- Rate-Limiting
- HSM/Enclave-Option (Vorbereitung)
"""

import logging
import re
import ctypes
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns für Secret-Detection
SECRET_PATTERNS = [
    re.compile(r'[0-9a-fA-F]{64}'),  # Private keys (256-bit hex)
    re.compile(r'xprv[a-zA-Z0-9]{107,108}'),  # BIP32 extended private keys
]


def detect_secrets(text: str) -> bool:
    """Detect if text contains potential secrets (PII/Keys)."""
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return True
    return False


def secure_wipe_string(s: str) -> None:
    """
    Überschreibe String im Speicher (best-effort).
    Python strings sind immutable, aber wir können versuchen,
    den Buffer zu überschreiben falls intern genutzt.
    """
    try:
        # Versuche Buffer zu überschreiben (nicht garantiert in Python)
        buf = (ctypes.c_char * len(s)).from_address(id(s))
        ctypes.memset(buf, 0, len(s))
    except Exception as e:
        logger.debug(f"Memory wipe failed (non-critical): {e}")


class WalletScannerSecurity:
    """Security utilities for wallet scanner"""
    
    def __init__(self):
        self.rate_limits: dict[str, list[float]] = {}  # user_id -> timestamps
    
    def check_rate_limit(self, user_id: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """
        Rate limiting: max_requests per window_seconds.
        Returns True if allowed, False if exceeded.
        """
        import time
        now = time.time()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Bereinige alte Timestamps
        self.rate_limits[user_id] = [
            ts for ts in self.rate_limits[user_id] if now - ts < window_seconds
        ]
        
        if len(self.rate_limits[user_id]) >= max_requests:
            return False
        
        self.rate_limits[user_id].append(now)
        return True
    
    def sanitize_for_audit(self, data: dict) -> dict:
        """
        Entferne sensible Daten aus Audit-Logs.
        Ersetzt Seeds/Keys durch Hashes.
        """
        sanitized = data.copy()
        
        if "seed_phrase" in sanitized:
            import hashlib
            hash_val = hashlib.sha256(sanitized["seed_phrase"].encode()).hexdigest()[:16]
            sanitized["seed_phrase"] = f"<redacted:hash={hash_val}>"
        
        if "private_key" in sanitized:
            import hashlib
            hash_val = hashlib.sha256(sanitized["private_key"].encode()).hexdigest()[:16]
            sanitized["private_key"] = f"<redacted:hash={hash_val}>"
        
        return sanitized
    
    def validate_input_safety(self, input_text: str) -> tuple[bool, Optional[str]]:
        """
        Validiere Input auf potenzielle Injections/XSS.
        Returns (is_safe, error_message).
        """
        # Basis-Validierung: keine SQL/Script-Tags
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onload=',
            r'DROP TABLE',
            r'INSERT INTO',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                return False, f"Input contains potentially dangerous pattern: {pattern}"
        
        return True, None


# Singleton
wallet_scanner_security = WalletScannerSecurity()
