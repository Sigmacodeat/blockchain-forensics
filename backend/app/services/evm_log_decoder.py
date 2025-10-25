"""
Einfache EVM Log Decoder Utility für bekannte Bridge-Events.
- Mappt topic0-Signaturen -> Eventnamen
- Bietet decode_event(log) -> {event_name, topic0}

Hinweis: Dies ist eine minimalistische Implementierung für Performance/Filterung.
Eine vollständige ABI-Decodierung kann später ergänzt werden.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import json

# Minimale Topic-Karte (topic0 -> Eventname)
# Beispiele: Deposit / Send / MessageSent Events gängiger Bridges
KNOWN_TOPICS: Dict[str, str] = {
    # Generic ERC20 Transfer
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer",
    # Stargate: SendToChain (Beispiel-Hash; Platzhalter falls variierend)
    "0x98ea5fcaedb8f558b5756fa0fe58f3d82405463e99e36fcff7bcac28cf383e84": "SendToChain",
    # Wormhole: LogMessagePublished
    "0x5fe5a0b2b1d5b6b6d9b2b71e1a92c9a1bde7b27fa8d7d8b6f9eb7a0f2c913b17": "LogMessagePublished",
    # Across: FundsDeposited
    "0x0c7b68e2b1b99c8cf5f7e7d7f6845a5704c0e6f76fce0c2f3e6f9f2ad3c2b0a4": "FundsDeposited",
}


def _load_env_topics() -> Dict[str, str]:
    """Lädt zusätzliche Topic-Mappings aus der Environment-Variable BRIDGE_TOPIC_MAP_JSON."""
    raw = os.getenv("BRIDGE_TOPIC_MAP_JSON", "{}")
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {str(k).lower(): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _load_file_topics() -> Dict[str, str]:
    """Lädt Topics aus backend/app/decoder_specs/bridge_topics.json (falls vorhanden)."""
    try:
        base = Path(__file__).resolve().parents[2] / "app" / "decoder_specs"
        p = base / "bridge_topics.json"
        if p.exists():
            data = json.loads(p.read_text())
            if isinstance(data, dict):
                return {str(k).lower(): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _load_event_specs() -> Dict[str, Dict[str, Any]]:
    """Lädt optionale, speziertere Event-Spezifikationen aus BRIDGE_EVENT_SPECS_JSON.
    Schema pro topic0:
    {
      "<topic0>": {
        "name": "SendToChain",
        "sender_index": 1,            # index in topics[]
        "receiver_index": 2,          # optional
        "amount_word_index": 0,       # 0-basiert im data 32-byte Wort-Array
        "token_is_contract": true     # ob token = log.address gesetzt werden soll
      }
    }
    """
    raw = os.getenv("BRIDGE_EVENT_SPECS_JSON", "{}")
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            out: Dict[str, Dict[str, Any]] = {}
            for k, v in data.items():
                if not isinstance(v, dict):
                    continue
                spec = {
                    "name": str(v.get("name") or KNOWN_TOPICS.get(str(k).lower()) or "unknown"),
                    "sender_index": v.get("sender_index"),
                    "receiver_index": v.get("receiver_index"),
                    "amount_word_index": v.get("amount_word_index"),
                    "token_is_contract": bool(v.get("token_is_contract", True)),
                }
                out[str(k).lower()] = spec
            return out
    except Exception:
        pass
    return {}


def _load_file_event_specs() -> Dict[str, Dict[str, Any]]:
    """Lädt Event-Spezifikationen aus backend/app/decoder_specs/bridge_event_specs.json (falls vorhanden)."""
    try:
        base = Path(__file__).resolve().parents[2] / "app" / "decoder_specs"
        p = base / "bridge_event_specs.json"
        if p.exists():
            raw = json.loads(p.read_text())
            if isinstance(raw, dict):
                out: Dict[str, Dict[str, Any]] = {}
                for k, v in raw.items():
                    if not isinstance(v, dict):
                        continue
                    spec = {
                        "name": str(v.get("name") or KNOWN_TOPICS.get(str(k).lower()) or "unknown"),
                        "sender_index": v.get("sender_index"),
                        "receiver_index": v.get("receiver_index"),
                        "amount_word_index": v.get("amount_word_index"),
                        "token_is_contract": bool(v.get("token_is_contract", True)),
                    }
                    out[str(k).lower()] = spec
                return out
    except Exception:
        pass
    return {}


def register_topics(mapping: Dict[str, str]) -> None:
    """Registriert zusätzliche topic0->Eventnamen Mappings zur Laufzeit."""
    for k, v in (mapping or {}).items():
        try:
            KNOWN_TOPICS[str(k).lower()] = str(v)
        except Exception:
            continue


# 1) File-basierte Mappings laden
_FILE_TOPICS = _load_file_topics()
if _FILE_TOPICS:
    register_topics(_FILE_TOPICS)

# 2) ENV-Topic-Mappings (override)
_ENV_TOPICS = _load_env_topics()
if _ENV_TOPICS:
    register_topics(_ENV_TOPICS)

"""
"""

# 3) Event-Spezifikationen laden: Datei zuerst, dann ENV override
EVENT_SPECS: Dict[str, Dict[str, Any]] = {}
try:
    _file_specs = _load_file_event_specs()
    if _file_specs:
        EVENT_SPECS.update(_file_specs)
    _env_specs = _load_event_specs()
    if _env_specs:
        EVENT_SPECS.update(_env_specs)
except Exception:
    EVENT_SPECS = {}


def get_event_name(topic0: Optional[str]) -> Optional[str]:
    if not topic0 or not isinstance(topic0, str):
        return None
    key = topic0.lower()
    return KNOWN_TOPICS.get(key)


def decode_event(log: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal-Decoding: erkennt Eventnamen anhand topic0 und liefert Metadaten zurück."""
    topics = log.get("topics") or []
    topic0 = topics[0] if topics else None
    event_name = get_event_name(topic0)
    return {
        "event_name": event_name,
        "topic0": (topic0.lower() if isinstance(topic0, str) else topic0),
    }


def _hex_to_int(x: Optional[str]) -> Optional[int]:
    if isinstance(x, str):
        try:
            return int(x, 16)
        except Exception:
            return None
    return None


def _normalize_topic_address(topic_hex: Optional[str]) -> Optional[str]:
    # topics encode indexed address as 32-byte right-padded; last 20 bytes are the address
    if not isinstance(topic_hex, str):
        return None
    h = topic_hex.lower()
    if h.startswith("0x"):
        h = h[2:]
    if len(h) == 64:
        return "0x" + h[-40:]
    if len(h) == 40:
        return "0x" + h
    return None


def decode_bridge_log(chain_id: str, contract_address: str, log: Dict[str, Any]) -> Dict[str, Any]:
    """Structured, ABI-lose Dekodierung häufiger Bridge-/Transfer-Logs.
    Liefert Felder: event_name, sender, receiver, amount (int), token (falls ermittelbar), confidence.
    """
    topics = log.get("topics") or []
    data = log.get("data") or "0x"
    topic0 = topics[0] if topics else None
    event_name = get_event_name(topic0)

    result: Dict[str, Any] = {
        "event_name": event_name,
        "sender": None,
        "receiver": None,
        "amount": None,
        "token": None,
        "confidence": 0.3,
    }

    # 1) Spezifikationen (falls via ENV konfiguriert)
    if isinstance(topic0, str):
        spec = EVENT_SPECS.get(topic0.lower())
        if spec:
            # Name ggf. überschreiben
            result["event_name"] = spec.get("name") or event_name

            # Sender/Empfänger aus topics
            si = spec.get("sender_index")
            if isinstance(si, int) and len(topics) > si:
                result["sender"] = _normalize_topic_address(topics[si])
            ri = spec.get("receiver_index")
            if isinstance(ri, int) and len(topics) > ri:
                result["receiver"] = _normalize_topic_address(topics[ri])

            # Amount aus data-Wort-Index
            wi = spec.get("amount_word_index")
            if isinstance(wi, int) and isinstance(data, str) and data.startswith("0x"):
                # Schneide in 32-Byte-Wörter
                hexdata = data[2:]
                words: List[str] = ["0x" + hexdata[i:i+64] for i in range(0, len(hexdata), 64)] if hexdata else []
                if 0 <= wi < len(words):
                    try:
                        result["amount"] = int(words[wi], 16)
                        result["confidence"] = max(result["confidence"], 0.8)
                    except Exception:
                        pass

            # Token-Setzung
            if bool(spec.get("token_is_contract", True)):
                result["token"] = contract_address

            # Wenn wir durch Spezifikation Felder gesetzt haben, Confidence erhöhen
            if any(result.get(k) for k in ("sender", "receiver", "amount")):
                result["confidence"] = max(result["confidence"], 0.85)
            # Kein frühzeitiges return: Erlaube nachgelagerte Heuristiken (z.B. ERC20 Transfer) die Confidence zu erhöhen

    # 2) Heuristik: ERC20 Transfer(address indexed from, address indexed to, uint256 value)
    if event_name == "Transfer" and len(topics) >= 3:
        sender = _normalize_topic_address(topics[1])
        receiver = _normalize_topic_address(topics[2])
        # data: 32-byte amount
        amount = None
        if isinstance(data, str) and data.startswith("0x") and len(data) >= 2 + 64:
            try:
                amount = int(data, 16)
            except Exception:
                amount = None
        result.update({
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "token": contract_address,
            "confidence": 0.95,
        })
        return result

    # 3) Generische Heuristik: Falls genau 1 indexed address und 32-byte amount im data
    # Versuch, sender aus topics[1] zu ziehen
    if len(topics) >= 2:
        cand_addr = _normalize_topic_address(topics[1])
        if cand_addr:
            result["sender"] = cand_addr
            result["confidence"] = max(result["confidence"], 0.5)
    # amount aus data, wenn 32-byte
    if isinstance(data, str) and data.startswith("0x") and (len(data) == 2 + 64 or len(data) == 2 + 128):
        try:
            result["amount"] = int(data[:66], 16)  # nutze erstes 32-Byte Wort
            result["confidence"] = max(result["confidence"], 0.6)
        except Exception:
            pass
    # token ist häufig das Log-Contract
    result["token"] = contract_address
    return result
