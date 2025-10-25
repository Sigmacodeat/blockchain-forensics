"""Enrichment Services

Lightweight __init__: vermeidet eager Imports (z.B. labels_service),
um Side-Effects während Test-Collection (Settings-Validation) zu verhindern.
Verbraucher sollen Module explizit importieren.
"""

__all__ = [
    "abi_decoder",
    "ABIDecoder",
    "labels_service",
    "LabelsService",
]
