# KYT Rule-DSL Leitfaden

Diese JSON-DSL wird in `monitor_rules.expression` verwendet und vom `RuleEngine` in `backend/app/compliance/rule_engine.py` ausgewertet.

- Unterstützte Operatoren:
  - Logik: `any`, `all`, `not`
  - Vergleiche: `>`, `>=`, `<`, `<=`, `==`
  - Feldvergleich: `{ "feld.pfad": { ">=": 2 } }` oder Literalgleichheit `{ "event_type": "bridge" }`
- Feldzugriff via Punktnotation: z.B. `metadata.bridge` oder `chains_involved`

## Beispiele

- Bridge-Aktivität erkennen
```json
{
  "event_type": "bridge"
}
```

- DEX-Swap erkennen
```json
{
  "event_type": "dex_swap"
}
```

- Cross-Chain Exposure: mind. 2 Chains und max. 3 Hops
```json
{
  "all": [
    { "chains_involved": { ">=": 2 } },
    { "cross_chain_hops": { "<=": 3 } }
  ]
}
```

- Zeitfenster (falls Event diese Felder trägt):
```json
{
  "all": [
    { "from_timestamp": { "==": "2024-01-01T00:00:00Z" } },
    { "to_timestamp":   { "==": "2024-12-31T23:59:59Z" } }
  ]
}
```

- Kombiniert (Bridge-Ereignis in Cross-Chain-Kontext):
```json
{
  "all": [
    { "event_type": "bridge" },
    { "chains_involved": { ">=": 2 } }
  ]
}
```

## Hinweise
- Die Event-Anreicherung im Monitor-Consumer (`backend/app/streaming/monitor_consumer.py`) setzt Felder wie `event_type`, `bridge`, `chain_from`, `chain_to`, `chains_involved`, `cross_chain_hops` best-effort.
- Komplexe Regeln sollten schrittweise getestet werden: `POST /api/v1/monitor/rules/validate` und `POST /api/v1/monitor/process-event`.
- Zeitliche Korrelationen (z. B. "dex_swap" gefolgt von "bridge" innerhalb eines Fensters) werden von der Korrelationsebene der Alert-Engine gehandhabt (`AlertEngine`), nicht von der einfachen DSL.
