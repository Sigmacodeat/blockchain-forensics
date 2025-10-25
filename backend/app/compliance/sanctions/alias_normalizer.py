from typing import Dict, Any, List, Tuple

# Very simple normalizer stub: lowercases names/aliases and trims

def normalize_entities_aliases(
    entities: List[Dict[str, Any]],
    aliases: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    def _norm(s: str) -> str:
        return s.strip().lower()

    for e in entities:
        if "canonical_name" in e and isinstance(e["canonical_name"], str):
            e["canonical_name_norm"] = _norm(e["canonical_name"])
    for a in aliases:
        if "value" in a and isinstance(a["value"], str):
            a["value_norm"] = _norm(a["value"])
    return entities, aliases
