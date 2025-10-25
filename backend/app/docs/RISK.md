# Risk Scoring

Einfaches Risk Scoring v1 kombiniert folgende Faktoren (0..1), aggregiert linear zu 0..100:

- watchlist: 1.0 wenn in Watchlist (Compliance-Service), sonst 0.0
- labels: Heuristischer Wert basierend auf Label-Kategorien (z. B. mixer/scam/exchange)
- taint: Platzhalter (derzeit 0.0 in TEST/OFFLINE)
- exposure: Normalisierte Exposure aus Neo4j (`get_address_exposure()`), Normalisierung via `x/(1+x)`
- graph: Optionaler Faktor aus Graph-Signalen (siehe unten)

## Graph-Signale (optional)

Aktivierbar mit `RISK_USE_GRAPH_SIGNALS=true`. Genutzte Signale aus `neo4j_client.get_address_graph_signals()`:

- avg_neighbor_taint: Durchschnittliche `taint_received` direkter Nachbarn
- high_risk_neighbor_ratio: Anteil Nachbarn mit `taint_received > 0.5`
- max_path_taint3: Maximale Pfad-Taint-Summe innerhalb 3 Hops, normalisiert via `x/(1+x)`

Aggregation: Gleichgewichtetes Mittel der drei Signale → `graph` (0..1). Gewichtung über `RISK_W_GRAPH`.

## Gewichte (Settings)

- RISK_W_WATCHLIST (Default 0.6)
- RISK_W_LABELS (Default 0.25)
- RISK_W_TAINT (Default 0.05)
- RISK_W_EXPOSURE (Default 0.10)
- RISK_W_GRAPH (Default 0.0)

Konfiguration über Umgebungsvariablen oder Settings. Bei fehlenden Werten greifen Defaults.

### Beispiel-.env

```
RISK_USE_GRAPH_SIGNALS=true
RISK_W_GRAPH=0.15
RISK_PERSIST_TO_GRAPH=true
```

## Persistierung

Mit `RISK_PERSIST_TO_GRAPH=true` wird der berechnete Score (0..100) auf `(:Address).risk_score` geschrieben.

## Verhalten Test/Offline

- TEST_MODE=1 oder OFFLINE_MODE=1:
  - `taint`, `exposure`, `graph` werden nicht aus Neo4j gelesen (0.0)
  - Service funktioniert ohne DB/Neo4j

## API

- GET `/api/v1/risk/address?chain=&address=` → `{ result: { chain, address, score, factors, categories, reasons } }`
- POST `/api/v1/risk/batch` → `{ results: [...] }`
- GET `/api/v1/risk/weights` → aktuelle Gewichte
- POST `/api/v1/risk/weights` → Gewichte setzen (nur TEST/DEBUG)
- PUT `/api/v1/risk/weights/admin` → Admin-gesichertes Setzen (JWT-Role `admin` oder `X-Admin: 1` im Dev), mit Audit-Log

## Erweiterungen (Roadmap)

- Bessere Exposure-Normalisierung (Percentiles/Log)
- Zeitliche/Volumen-Signale
- Graph-basierte Heuristiken (Cluster/Paths)
- Kalibrierung/Thresholds
