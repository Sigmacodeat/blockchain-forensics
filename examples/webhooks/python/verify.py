import hmac
import hashlib
import time
from typing import Dict


def verify_webhook_v2(body: bytes, headers: Dict[str, str], secret: str) -> bool:
    ts = headers.get("x-webhook-timestamp")
    sigv2 = (headers.get("x-webhook-signature-v2") or "").replace("sha256=", "")
    if not ts or not sigv2:
        return False
    try:
        ts_int = int(ts)
    except Exception:
        return False
    # Replay window 5min
    if abs(int(time.time()) - ts_int) > 300:
        return False
    base = f"{ts}.{body.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sigv2)


def verify_webhook_legacy(body: bytes, headers: Dict[str, str], secret: str) -> bool:
    sig = (headers.get("x-webhook-signature") or "").replace("sha256=", "")
    if not sig:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
