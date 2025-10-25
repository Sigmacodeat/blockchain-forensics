import time
from app.services.intel_webhook_verifier import verify_signature


def _hdrs(**k):
    return {k_.replace("_","-"): v for k_, v in {**k}.items()}


def test_legacy_signature_valid():
    secret = "s3cr3t"
    body = '{"a":1}'
    import hmac
    import hashlib
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    headers = _hdrs(**{"X_Webhook_Signature": f"sha256={sig}"})
    assert verify_signature(secret, headers, body) is True


def test_legacy_signature_invalid():
    secret = "s3cr3t"
    body = '{"a":1}'
    headers = _hdrs(**{"X_Webhook_Signature": "sha256=deadbeef"})
    assert verify_signature(secret, headers, body) is False


def test_v2_signature_valid():
    secret = "s3cr3t"
    body = '{"event":"ok"}'
    ts = str(int(time.time()))
    base = f"{ts}.{body}"
    import hmac
    import hashlib
    sig = hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    headers = _hdrs(
        X_Webhook_Timestamp=ts,
        X_Webhook_Signature_V2=f"sha256={sig}",
    )
    assert verify_signature(secret, headers, body) is True


def test_v2_signature_timestamp_skew():
    secret = "s3cr3t"
    body = '{}'
    # Too old timestamp (10 minutes)
    ts = str(int(time.time()) - 600)
    base = f"{ts}.{body}"
    import hmac
    import hashlib
    sig = hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    headers = _hdrs(
        X_Webhook_Timestamp=ts,
        X_Webhook_Signature_V2=f"sha256={sig}",
    )
    assert verify_signature(secret, headers, body) is False
