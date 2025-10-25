# Cross-Chain Bridge Detection & Analysis

## Übersicht

Das Bridge Detection Modul ermöglicht forensische Analyse von Cross-Chain-Transaktionen über 10+ Major Bridges. Es identifiziert Bridge-Interaktionen, verknüpft Adressen über Chains hinweg und ermöglicht Multi-Hop-Tracing für gerichtsverwertbare Evidenz.

## Unterstützte Bridges

### Layer-1 & General Purpose Bridges

| Bridge | Chains | Pattern | Status |
|--------|---------|---------|--------|
| **Wormhole** | Ethereum, Solana, Polygon, BSC, Avalanche, etc. | Lock-Mint | ✅ |
| **Multichain (Anyswap)** | Ethereum, Polygon, Fantom, etc. | Lock-Mint | ✅ (Exploited 2023) |
| **Synapse** | Ethereum, Polygon, Arbitrum, etc. | Lock-Mint | ✅ |
| **Celer cBridge** | Ethereum, Polygon, BSC, etc. | Liquidity Pool | ✅ |
| **THORChain** | Ethereum, BSC, Bitcoin, etc. | AMM Bridge | ✅ |

### Liquidity Bridges

| Bridge | Chains | Pattern | Status |
|--------|---------|---------|--------|
| **Stargate (LayerZero)** | Ethereum, Polygon, Arbitrum, Optimism, etc. | Liquidity Pool | ✅ |
| **Hop Protocol** | Ethereum, Polygon, Arbitrum, Optimism | Liquidity Pool | ✅ |
| **Across** | Ethereum, Polygon, Arbitrum, Optimism | Optimistic Relay | ✅ |

### Rollup Bridges

| Bridge | Chains | Pattern | Status |
|--------|---------|---------|--------|
| **Arbitrum Bridge** | Ethereum ↔ Arbitrum | Lock-Mint | ✅ |
| **Optimism Bridge** | Ethereum ↔ Optimism | Lock-Mint | ✅ |
| **Polygon PoS Bridge** | Ethereum ↔ Polygon | Lock-Mint | ✅ |

## Detection Methoden

### 1. Contract Address Detection

Identifiziert Bridges anhand bekannter Contract-Adressen:

```python
# Wormhole Token Bridge auf Ethereum
WORMHOLE_ETH = "0x3ee18b2214aff97000d974cf647e7c347e8fa585"

# Automatische Detection
if tx.to_address == WORMHOLE_ETH:
    bridge = "Wormhole"
    pattern = "lock_mint"
```

**Vorteile:**
- Zuverlässig für bekannte Bridges
- Geringe False-Positive-Rate
- Schnell

**Nachteile:**
- Erfordert Registry-Updates für neue Bridges
- Verpasst unbekannte Bridges

### 2. Event Signature Detection

Identifiziert Bridges anhand von Event-Signaturen (Ethereum):

```python
# Wormhole LogMessagePublished Event
WORMHOLE_EVENT = "0x6eb224fb001ed210e379b335e35efe88672a8ce935d981a6896b27ffdf52a3b2"

# Detection via Event Logs
for log in tx.logs:
    if log.topics[0] == WORMHOLE_EVENT:
        bridge = "Wormhole"
```

**Vorteile:**
- Erkennt Bridge-Interaktionen auch bei Proxy-Contracts
- Detaillierte Metadaten verfügbar

### 3. Program ID Detection (Solana)

Identifiziert Bridges anhand von Program IDs:

```python
# Wormhole Core Program auf Solana
WORMHOLE_SOL = "worm2zkamqrctqlvr4j3yk87ugmqhjf32gzvwe7v9"

# Detection via Instructions
if program_id in tx.instructions:
    bridge = "Wormhole"
    chain_to = decode_wormhole_target(tx)
```

**Vorteile:**
- Solana-spezifisch optimiert
- Erkennt SPL Token Bridges

### 4. Metadata Heuristics

Inferiert Ziel-Chains aus Transaction-Metadata:

```python
# Wormhole Chain ID Mapping
WORMHOLE_CHAINS = {
    1: "solana",
    2: "ethereum",
    5: "polygon",
    23: "arbitrum",
}

chain_to = WORMHOLE_CHAINS.get(metadata.chain_id, "unknown")
```

## API Endpoints

### GET /api/v1/bridge/supported-bridges

Listet alle unterstützten Bridges.

**Response:**
```json
{
  "total_bridges": 11,
  "supported_chains": ["ethereum", "solana", "polygon"],
  "bridges": [
    {
      "bridge_name": "Wormhole",
      "chain": "ethereum",
      "contract_count": 2,
      "pattern_type": "lock_mint",
      "metadata": {
        "website": "wormhole.com",
        "type": "generic_bridge"
      }
    }
  ]
}
```

### POST /api/v1/bridge/flow-analysis

Analysiert Cross-Chain-Flow für eine Adresse.

**Request:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "max_hops": 5
}
```

**Response:**
```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "total_flows": 3,
  "max_hops_found": 2,
  "flows": [
    {
      "path_length": 2,
      "hops": [
        {
          "bridge": "Wormhole",
          "chain_from": "ethereum",
          "chain_to": "solana",
          "tx_hash": "0xabc...",
          "timestamp": "2025-10-10T12:00:00Z"
        },
        {
          "bridge": "Stargate",
          "chain_from": "solana",
          "chain_to": "polygon",
          "tx_hash": "5J8K9L...",
          "timestamp": "2025-10-10T12:05:00Z"
        }
      ],
      "start_address": "0x742d35Cc...",
      "end_address": "polygon_address_123"
    }
  ],
  "analysis_timestamp": "2025-10-11T14:30:00Z"
}
```

### GET /api/v1/bridge/cross-chain-link

Findet verknüpfte Adresse auf Target-Chain.

**Query Parameters:**
- `source_address`: Quell-Adresse
- `source_chain`: Quell-Chain (ethereum, solana, etc.)
- `target_chain`: Ziel-Chain

**Response:**
```json
{
  "source_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "source_chain": "ethereum",
  "target_chain": "solana",
  "found_links": 1,
  "links": [
    {
      "linked_address": "ABC123DEF456...",
      "bridge_name": "Wormhole",
      "tx_hash": "0xabc...",
      "timestamp": "2025-10-10T12:00:00Z"
    }
  ]
}
```

### GET /api/v1/bridge/statistics

Bridge-Nutzungsstatistiken aus Neo4j.

**Response:**
```json
{
  "total_bridge_transactions": 1523,
  "unique_addresses": 842,
  "top_bridges": [
    {
      "bridge_name": "Wormhole",
      "chain_from": "ethereum",
      "chain_to": "solana",
      "transaction_count": 456
    }
  ],
  "chain_distribution": {
    "ethereum": 789,
    "solana": 456,
    "polygon": 278
  }
}
```

## Neo4j Graph Struktur

### Nodes

```cypher
(:Address {
  address: "0x742d35Cc...",
  chain: "ethereum",
  created_at: datetime(),
  risk_score: 0.3
})
```

### Relationships

```cypher
(:Address)-[:BRIDGE_LINK {
  bridge: "Wormhole",
  chain_from: "ethereum",
  chain_to: "solana",
  tx_hash: "0xabc...",
  timestamp: datetime()
}]->(:Address)
```

### Queries

**Alle Bridge-Transaktionen einer Adresse:**
```cypher
MATCH (a:Address {address: $address})-[r:BRIDGE_LINK]->(dest:Address)
RETURN r.bridge, r.chain_from, r.chain_to, r.tx_hash, r.timestamp
ORDER BY r.timestamp DESC
```

**Multi-Hop-Pfade finden:**
```cypher
MATCH path = (start:Address {address: $address})-[:BRIDGE_LINK*1..5]->(dest:Address)
RETURN path,
       [rel in relationships(path) | {
         bridge: rel.bridge,
         chain_from: rel.chain_from,
         chain_to: rel.chain_to
       }] as hops
```

**Top Bridges nach Volumen:**
```cypher
MATCH ()-[r:BRIDGE_LINK]->()
WITH r.bridge AS bridge_name, count(*) AS tx_count
RETURN bridge_name, tx_count
ORDER BY tx_count DESC
LIMIT 10
```

## Forensische Anwendungsfälle

### 1. Geldwäsche-Untersuchung

**Szenario:** Verdächtige Adresse nutzt Bridges zur Verschleierung.

**Vorgehen:**
```python
# 1. Identifiziere Bridge-Transaktionen
response = await client.get(
    f"/api/v1/bridge/address/{suspect_address}/bridges"
)

# 2. Analysiere Multi-Hop-Flow
flow = await client.post("/api/v1/bridge/flow-analysis", json={
    "address": suspect_address,
    "max_hops": 5
})

# 3. Finde verknüpfte Adressen
for hop in flow["flows"][0]["hops"]:
    link = await client.get("/api/v1/bridge/cross-chain-link", params={
        "source_address": suspect_address,
        "source_chain": hop["chain_from"],
        "target_chain": hop["chain_to"]
    })
```

**Evidenz:**
- Bridge-Namen (z.B. Wormhole, Multichain)
- Timestamps (gerichtsverwertbar)
- Verknüpfte Adressen über alle Chains
- Transaction Hashes als Proof

### 2. Asset Recovery

**Szenario:** Gestohlene Gelder über Bridge transferiert.

**Vorgehen:**
```python
# Trace von Ethereum zu Solana
result = await client.get("/api/v1/bridge/cross-chain-link", params={
    "source_address": stolen_funds_eth_address,
    "source_chain": "ethereum",
    "target_chain": "solana"
})

solana_address = result["links"][0]["linked_address"]
# → Freezing Order auf Solana möglich
```

### 3. Compliance Screening

**Szenario:** KYC/AML Check für Multi-Chain-Nutzer.

**Vorgehen:**
```python
# Alle genutzten Chains identifizieren
flow = await client.post("/api/v1/bridge/flow-analysis", json={
    "address": user_address,
    "max_hops": 10
})

chains_used = set()
for flow_path in flow["flows"]:
    for hop in flow_path["hops"]:
        chains_used.add(hop["chain_from"])
        chains_used.add(hop["chain_to"])

# → Compliance-Check auf allen Chains erforderlich
```

## Performance & Skalierung

### Caching

```python
# Registry wird beim Start geladen (< 1ms)
bridges = BridgeRegistry.BRIDGES  # In-Memory

# Neo4j-Queries mit Indexes
CREATE INDEX ON :Address(address)
CREATE INDEX ON :BRIDGE_LINK(timestamp)
```

### Rate Limiting

Bridge-Detection ist RPC-schonend:
- Contract-Address-Matching: O(1) Lookup
- Event-Signature-Matching: Lokale Daten
- Nur Neo4j-Queries für Flow-Analyse

### Batch Processing

```python
# Mehrere Adressen parallel analysieren
addresses = ["0x123...", "0x456...", "0x789..."]
tasks = [
    bridge_detector.analyze_bridge_flow(addr, max_hops=3)
    for addr in addresses
]
results = await asyncio.gather(*tasks)
```

## Integration mit Tracing

Bridge-Detection integriert automatisch mit Transaction Tracing:

```python
# In tracer.py
from app.bridge.bridge_detector import bridge_detector

async def _enrich_transaction(tx: Transaction):
    # Bridge Detection
    bridge_data = await bridge_detector.detect_bridge(tx)
    
    if bridge_data:
        tx.labels.append(f"Bridge: {bridge_data['bridge_name']}")
        tx.metadata["bridge"] = bridge_data
        
        # Persist cross-chain link
        await persist_bridge_link(
            from_address=tx.from_address,
            to_address=bridge_data.get("destination_address"),
            bridge=bridge_data["bridge_name"],
            chain_from=bridge_data["chain_from"],
            chain_to=bridge_data["chain_to"],
            tx_hash=tx.tx_hash,
            timestamp_iso=tx.timestamp.isoformat()
        )
```

## Erweiterung für neue Bridges

### Schritt 1: Bridge-Signature hinzufügen

```python
# In bridge_detector.py
BridgeRegistry.BRIDGES.append(
    BridgeSignature(
        bridge_name="New Bridge",
        chain="ethereum",
        contract_addresses={
            "0xnewbridge123",
        },
        event_signatures={
            "0xevent_hash_123",
        },
        pattern_type="lock_mint",
        metadata={"website": "newbridge.io"}
    )
)
```

### Schritt 2: Tests hinzufügen

```python
def test_detect_new_bridge():
    sig = BridgeRegistry.get_signature_by_address(
        "0xnewbridge123",
        "ethereum"
    )
    assert sig.bridge_name == "New Bridge"
```

### Schritt 3: Deployment

```bash
# Tests ausführen
pytest tests/test_bridge_detector.py -v

# API neu starten
uvicorn app.main:app --reload
```

## Sicherheit & Validierung

### Input Validation

Alle Adressen werden normalisiert:
```python
address = address.lower()  # Ethereum: lowercase
```

### Rate Limiting

Bridge API nutzt globales Rate Limiting:
- 60 requests/min für Standard-User
- 1000 requests/min für Analyst-Role

### Error Handling

Graceful Degradation bei DB-Ausfällen:
```python
try:
    results = await neo4j_client.query(...)
except Exception as e:
    logger.error(f"Neo4j error: {e}")
    return {"total_flows": 0, "error": str(e)}
```

## Bekannte Einschränkungen

1. **Neue Bridges:** Erfordern manuelle Registry-Updates
2. **Private Bridges:** Werden nicht erkannt
3. **Destination Address:** Nicht immer ableitbar (Heuristiken erforderlich)
4. **Chain ID Mapping:** Nicht alle Chain IDs vollständig gemappt

## Roadmap

- [ ] Automatische Bridge-Discovery via On-Chain-Daten
- [ ] ML-basierte Pattern-Erkennung für unbekannte Bridges
- [ ] Real-Time-Monitoring via WebSocket
- [ ] Erweiterte Heuristiken für Destination Address Inference
- [ ] Support für 30+ weitere Bridges (Connext, Axelar, etc.)

## Support & Debugging

### Logs

```bash
# Bridge Detection Logs
docker-compose logs backend | grep "Bridge detected"

# Neo4j Errors
docker-compose logs neo4j | grep "ERROR"
```

### Health Check

```bash
curl http://localhost:8000/api/v1/bridge/health
```

### Neo4j Browser

```
http://localhost:7474
User: neo4j
Password: forensics_password_change_me

# Test Query
MATCH ()-[r:BRIDGE_LINK]->() RETURN count(r)
```

---

**Version:** 1.0.0  
**Stand:** 11.10.2025  
**Status:** ✅ Production Ready
