"""
Intel Webhook Signature Verifier
================================

Verifies inbound webhook signatures using either legacy body-only HMAC
(X-Webhook-Signature) or timestamped V2 (X-Webhook-Timestamp + X-Webhook-Signature-V2).
"""
from __future__ import annotations

import hmac
import hashlib
import time
from typing import Mapping, Optional

ALLOWED_CLOCK_SKEW_SECONDS = 300  # 5 minutes


def _parse_sig(header_value: Optional[str]) -> Optional[str]:
    if not header_value:
        return None
    try:
        algo, sig = header_value.split("=", 1)
        if algo.lower() != "sha256":
            return None
        return sig.strip()
    except Exception:
        return None


def verify_signature(secret: str, headers: Mapping[str, str], body_json: str) -> bool:
    """Verify inbound webhook signature.

    Supports:
    - Legacy: X-Webhook-Signature: "sha256=<hex>" computed over body
    - V2: X-Webhook-Timestamp + X-Webhook-Signature-V2: sha256 over "<ts>.<body>"
    """
    if not secret:
        return False

    # Normalize headers (case-insensitive lookup)
    norm_headers = {k.lower(): v for k, v in headers.items()}

    # Prefer V2 with timestamp (replay-safe)
    ts = norm_headers.get("x-webhook-timestamp")
    sig_v2_header = norm_headers.get("x-webhook-signature-v2")
    sig_v2 = _parse_sig(sig_v2_header)

    if ts and sig_v2:
        try:
            ts_int = int(ts)
        except Exception:
            return False
        now = int(time.time())
        if abs(now - ts_int) > ALLOWED_CLOCK_SKEW_SECONDS:
            return False
        base_string = f"{ts}.{body_json}"
        expected_v2 = hmac.new(secret.encode(), base_string.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_v2, sig_v2)

    # Fallback to legacy body-only signature
    sig_header = norm_headers.get("x-webhook-signature")
    sig_legacy = _parse_sig(sig_header)
    if not sig_legacy:
        return False
    expected_legacy = hmac.new(secret.encode(), body_json.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_legacy, sig_legacy)
