"""Konfigurationspaket mit Settings und Pricing-Helpern."""

from pathlib import Path
import importlib.util
import sys

from .pricing import (
    get_plan_config,
    calculate_crypto_amount,
    get_all_plans,
    get_currency,
)

def _load_fallback_settings():
    cfg_path = Path(__file__).resolve().parent.parent / "config.py"
    if not cfg_path.exists():
        return None

    module_name = "app._fallback_config"
    spec = importlib.util.spec_from_file_location(module_name, cfg_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, "settings", None)


try:  # Optionales Settings-Modul laden, falls vorhanden
    from .settings import settings  # type: ignore  # noqa: F401
except ImportError:
    fallback = _load_fallback_settings()
    settings = fallback  # type: ignore

__all__ = [
    "get_plan_config",
    "calculate_crypto_amount",
    "get_all_plans",
    "get_currency",
    "settings",
]
