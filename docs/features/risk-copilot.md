# Risk Copilot – State-of-the-Art Live-Risk-Streaming

## Übersicht

Der **Risk Copilot** ist ein Live-Risk-Scoring-Widget, das SSE (Server-Sent Events) nutzt, um Echtzeit-Risikobewertungen für Blockchain-Adressen zu liefern. Die Implementierung folgt modernsten UX- und Performance-Patterns.

## Features

### Backend (`backend/app/api/v1/risk.py`)

- **SSE-Streaming-Endpoint**: `GET /api/v1/risk/stream?chain=&address=`
- **Events**:
  - `risk.ready` – Verbindung hergestellt
  - `risk.typing` – Scoring läuft
  - `risk.error` – Fehler (z.B. `invalid_address`, `connection_error`)
  - `risk.result` – Ergebnis mit `score`, `categories`, `reasons`, `factors`
- **Rate-Limiting**: Pro Client (IP+Session), 60 Requests/Min
- **Disconnect-Detection**: `request.is_disconnected()` verhindert Ghost-Streams
- **Validierung**: Ethereum-Adressformat-Check, weitere Chains erweiterbar

### Frontend Hook (`frontend/src/hooks/useRiskStream.ts`)

- **EventSource-Management**: Auto-Start, Cleanup bei Unmount
- **State-Tracking**: `connected`, `loading`, `error`, `score`, `categories`, `reasons`, `factors`
- **Error-Handling**: Parse-Errors, Connection-Errors, Invalid-Address
- **Typed Events**: Vollständige TypeScript-Typisierung

### Frontend Komponente (`frontend/src/components/RiskCopilot.tsx`)

#### Drei Varianten

1. **`badge`** – Ultra-kompakt (Dot + Score)
   - Für Inline-Nutzung in Listen
   - Minimal: 2×2px Dot, Score-Zahl
   - Animierte Pulse während Loading

2. **`compact`** – Single-Line (Dot + Score + Top-2-Kategorien)
   - Für Adresslisten (Investigator)
   - Zeigt bis zu 2 Kategorien + "+X" Counter
   - Error-Icon bei Fehler

3. **`full`** – Complete Details (Dot + Score + Alle Kategorien + Reasons + Factors)
   - Für dedizierte Risk-Panels (Trace-Seite)
   - Vollständige Reasons-Liste
   - Factors-Grid (2-spaltig)
   - Skeleton-States während Loading

#### UX-Features

- **Adaptive Farben**:
  - Grün (0-19): Niedrig
  - Gelb (20-39): Mittel-Niedrig
  - Orange (40-59): Mittel
  - Rot-Orange (60-79): Hoch
  - Rot (80-100): Kritisch
  - Grau: Unbekannt/Lädt
- **Loading-States**: Pulse-Animationen auf Dot, Skeleton-Text für Score
- **Error-States**: Icon + Meldung (z.B. "⚠️ invalid_address")
- **Dark-Mode**: Vollständig responsive für Light/Dark

## Integration

### Trace-Seite (`frontend/src/app/(dashboard)/trace/page.tsx`)

```tsx
<RiskCopilot chain={params.chain} address={params.source} />
```

- **Kontext**: Dedicated Card unterhalb der Trace-Konfiguration
- **Variante**: `full` (Standard)
- **Nutzen**: Analyst sieht sofort Risk-Score der Source-Adresse

### Investigator-Seite (`frontend/src/app/(dashboard)/investigator/page.tsx`)

```tsx
<RiskCopilot chain={selectedChain} address={addr} variant="compact" />
```

- **Kontext**: Neben jeder Adresse in der Adressliste
- **Variante**: `compact`
- **Nutzen**: Schneller Überblick über Risiken aller Case-Adressen

## API-Beispiele

### SSE-Request

```bash
curl -N "http://localhost:8000/api/v1/risk/stream?chain=ethereum&address=0xabc..."
```

### Event-Sequence

```
event: risk.ready
data: {"ok":true}

event: risk.typing
data: {"ok":true}

event: risk.result
data: {"chain":"ethereum","address":"0xabc...","score":0.75,"factors":{"watchlist":0.8,"taint":0.7},"categories":["mixer"],"reasons":["High taint from mixer","Watchlist match"]}
```

### Error-Event

```
event: risk.error
data: {"detail":"invalid_address"}
```

## Performance

- **SSE-Backpressure**: `await asyncio.sleep(0)` zwischen Events
- **EventSource Auto-Reconnect**: Browser-native Retry-Logic
- **Adaptive Chunking**: Dynamische Chunk-Größen im Backend (future)
- **Rate-Limit**: 429 mit `Retry-After` Header

## Best Practices

### Frontend

- **Cleanup**: `useEffect` Return-Funktion schließt EventSource
- **Memoization**: Komponente nutzt `React.memo` (optional, zukünftig)
- **Skeleton**: Loading-States mit Pulse-Animationen
- **Accessibility**: ARIA-Labels für Screen-Reader (zukünftig)

### Backend

- **Idempotenz**: Mehrfache Requests für dieselbe Adresse sind sicher
- **Caching**: Risk-Service kann Scores cachen (optional)
- **Monitoring**: Metrics via `COMPLIANCE_REQUESTS`, `COMPLIANCE_LATENCY`

## Erweiterungen (Roadmap)

- **[P1] Tooltips**: Hover-Details für Faktoren
- **[P1] History**: Score-Timeline (sparkline)
- **[P2] Alerts**: Threshold-basierte Benachrichtigungen
- **[P2] Multi-Chain**: Automatische Chain-Detection aus Adressformat
- **[P3] AI-Explanation**: LLM-generierte Erklärungen für Score-Faktoren

## Testing

### Backend

```bash
# Minimal-Test
pytest backend/tests/test_risk_stream.py -v
```

Erwartete Tests:
- `test_risk_stream_valid_address` → 200, `risk.result`
- `test_risk_stream_invalid_address` → 200, `risk.error` mit `invalid_address`
- `test_risk_stream_rate_limit` → 429

### Frontend

```bash
# Mock EventSource
npm run test src/hooks/useRiskStream.test.ts
```

Erwartete Tests:
- `renders badge variant correctly`
- `shows loading state during scoring`
- `displays error message on error event`

## Status

- ✅ Backend SSE-Endpoint implementiert
- ✅ Frontend Hook mit Auto-Cleanup
- ✅ Komponente mit 3 Varianten (badge/compact/full)
- ✅ Integration in Trace-Seite (full)
- ✅ Integration in Investigator-Seite (compact)
- ✅ Loading/Error-States
- ✅ Dark-Mode Support
- ⏳ Unit-Tests (optional)
- ⏳ Tooltips/Hover-Details (optional)

## Maintainer Notes

- **Backend**: `backend/app/api/v1/risk.py` – `risk_stream()` Funktion
- **Frontend Hook**: `frontend/src/hooks/useRiskStream.ts`
- **Frontend Komponente**: `frontend/src/components/RiskCopilot.tsx`
- **Integration**: Trace + Investigator Pages

Für Fragen: siehe `COMPLETE_PROJECT_STATUS_2025.md`
