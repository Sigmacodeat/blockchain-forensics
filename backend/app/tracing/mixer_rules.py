"""
Mixer Demixing Rules (stubs)
Defines known mixer behaviors and taint-demixing hints
"""
from typing import Dict, List, Any

MIXER_RULES: List[Dict[str, Any]] = [
    {
        "name": "Tornado Cash",
        "chain": "ethereum",
        "denominations": [0.1, 1, 10, 100],  # ETH denominations (example)
        "heuristics": [
            "entry_exit_time_window",
            "fixed_denomination_matching",
            "self-deposit detection",
            "multi-exit fan-out",
        ],
        "status": "heuristics",
    },
    {
        "name": "ChipMixer",
        "chain": "bitcoin",
        "heuristics": [
            "utxo peeling",
            "chip reassembly",
            "time bucket clustering",
        ],
        "status": "planned",
    },
]


def list_mixer_rules() -> List[Dict[str, Any]]:
    return MIXER_RULES
