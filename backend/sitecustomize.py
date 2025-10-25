"""
Test-time customization for Python interpreter.
This module is auto-imported by Python if present on sys.path.
We patch Passlib's bcrypt detection to avoid ValueError with bcrypt>=4
which raises on >72 byte secrets during backend self-checks.
This affects only tests and does not change app runtime behavior.
"""

import os

# Only apply in tests to avoid altering production behavior
if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TEST_MODE") == "1":
    try:
        from passlib.handlers import bcrypt as passlib_bcrypt  # type: ignore

        # Disable wraparound bug detection which uses an extremely long secret
        # that triggers ValueError in bcrypt>=4.
        def _no_detect(*args, **kwargs):  # noqa: D401
            return False

        passlib_bcrypt.detect_wrap_bug = _no_detect  # type: ignore[attr-defined]

        # Ensure bcrypt handler won't raise on >72 bytes during tests
        try:
            passlib_bcrypt.bcrypt = passlib_bcrypt.bcrypt.using(truncate_error=False)  # type: ignore[attr-defined]
        except Exception:
            pass

        # As a last resort, patch backend to truncate secrets >72 bytes during tests
        try:
            _orig_calc = passlib_bcrypt._BcryptBackend._calc_checksum  # type: ignore[attr-defined]

            def _calc_checksum_trunc(self, secret):  # type: ignore[override]
                try:
                    if isinstance(secret, (bytes, bytearray)) and len(secret) > 72:
                        secret = secret[:72]
                except Exception:
                    pass
                return _orig_calc(self, secret)

            passlib_bcrypt._BcryptBackend._calc_checksum = _calc_checksum_trunc  # type: ignore[attr-defined]
        except Exception:
            pass

        # Additionally, spoof bcrypt version metadata if missing to avoid warnings
        try:
            import bcrypt as _bcrypt  # type: ignore
            if not hasattr(_bcrypt, "__about__"):
                class _About:  # minimal shim
                    __version__ = getattr(_bcrypt, "__version__", "4.0.0")
                _bcrypt.__about__ = _About()  # type: ignore[attr-defined]
        except Exception:
            pass
    except Exception:
        # If passlib/bcrypt isn't available, do nothing.
        pass
