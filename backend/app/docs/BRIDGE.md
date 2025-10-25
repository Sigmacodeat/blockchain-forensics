# Bridge Detection & Cross-Chain Links

Dieses Dokument beschreibt, wie Bridge-Transaktionen erkannt und als Cross-Chain-Links persistiert werden.

## Architektur-Überblick

- Adapter (z. B. `app/adapters/ethereum_adapter.py`, `app/adapters/solana_adapter.py`) markieren potenzielle Bridge-Transaktionen.
- Tracer (`app/tracing/tracer.py`) übernimmt Bridge-Metadaten aus Roh-TXs oder nutzt Label-Heuristiken, um `TraceEdge.event_type="bridge"` zu setzen.
- Persist (`app/api/v1/trace.py::save_trace_to_graph`) ruft bei Bridge-Kanten `app/bridge/hooks.py::persist_bridge_link()` auf und legt `:BRIDGE_LINK`-Kanten in Neo4j an.

## Konfiguration

### Ethereum

Um bekannte Bridge-Targets/Methoden zu pflegen, setze in `.env` (oder Umgebung):

- `BRIDGE_CONTRACTS_ETH` — Kommagetrennte Liste von Ziel-Contract-Adressen (lowercase oder checksummed)
- `BRIDGE_METHOD_SELECTORS` — Liste von Method-Selectoren (4-Byte Signaturen), z. B. `[
  "0x...",
  "0x..."
]`

Beispiel `.env`:

```
BRIDGE_CONTRACTS_ETH=0x3ee18b2214aff97000d974cf647e7c347e8fa585,0x8731d54e9d02c286767d56ac03e8037c07e01e98
BRIDGE_METHOD_SELECTORS=["0x12345678","0xabcdef12"]
```

Der Ethereum-Adapter (`_determine_event_type`) setzt `event_type="bridge"`, wenn die Zieladresse in `BRIDGE_CONTRACTS_ETH` ist oder der Method-Selector in `BRIDGE_METHOD_SELECTORS` vorkommt.

### Solana

- `BRIDGE_PROGRAMS_SOL` — Liste bekannter Program IDs, die Bridge-Operationen indizieren.

Beispiel `.env`:

```
BRIDGE_PROGRAMS_SOL=["wormDTUJr1n2U4tQ1Fq1Rk3LtWgD5S8v6vG7t9p5p6","Bridge1p5vGZ1kWormholeExample111111111111111"]
```

Der Solana-Adapter markiert `event_type="bridge"`, wenn eine Program ID in `accountKeys` oder `instructions/innerInstructions` vorkommt und speichert die Program-ID im `metadata.bridge_program`.

## TraceEdge Metadaten

`app/tracing/models.py::TraceEdge` enthält optionale Felder:

- `event_type` — z. B. `bridge`
- `bridge` — Name/ID der Bridge (falls verfügbar)
- `chain_from`, `chain_to` — Ketteninformationen für Cross-Chain-Linking

Diese Felder können vom Adapter/Enrichment gesetzt werden. Fehlen sie, versucht der Tracer eine Heuristik über Labels (`wormhole`, `stargate`, `layerzero`, ...).

## Persistierung in Neo4j

`app/db/neo4j_client.py::create_bridge_link()` erzeugt `(:Address)-[:BRIDGE_LINK {bridge, chain_from, chain_to, tx_hash, timestamp}]→(:Address)`. Der Aufruf ist best-effort und im `TEST_MODE/OFFLINE_MODE` ein No-Op.

## Tests

- `tests/test_bridge_persist.py` — prüft, dass der Bridge-Hook bei markierter Kante aufgerufen wird.
- `tests/test_solana_bridge_detection.py` — prüft Bridge-Erkennung über Program IDs.

## Hinweise

- Listen (`BRIDGE_CONTRACTS_ETH`, `BRIDGE_PROGRAMS_SOL`) sollten regelmäßig gepflegt werden (Feeds/OSINT).
- Beispiele (prüfen/aktualisieren):
  - Ethereum Contracts (Beispiele): Wormhole `0x3ee18b2214aff97000d974cf647e7c347e8fa585`, Stargate Router (Chain-spezifisch), Multichain (historisch, ggf. deprecated)
  - Method-Selectoren: bridging/lock/mint Funktionen der jeweiligen Bridges (ABI-Quellen: Etherscan, 4byte.directory)
  - Solana Programs (Beispiele): Wormhole Core `wormDTUJr1n2U4tQ1Fq1Rk3LtWgD5S8v6vG7t9p5p6` (Beispiel), Token Bridge Program-ID laut offizieller Doku
- Für präzisere Erkennung: ABI-Decode (EVM) und Program-Parsing (Solana) einführen.
- Cross-Chain `chain_from/chain_to` können aus Kontext/Adapter hergeleitet werden (Roadmap).
- Validierung:
  - Unit-Tests für Heuristik (siehe `tests/test_solana_bridge_detection.py`).
  - E2E-Test: reale Bridge-TXs als Fixtures, Prüfung von `event_type="bridge"` und `:BRIDGE_LINK` Persist.
