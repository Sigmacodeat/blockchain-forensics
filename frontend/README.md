# Blockchain Forensics Platform - Frontend

React + TypeScript + TailwindCSS Frontend für die ultimative Blockchain-Analyse-Plattform.

## Tech Stack

- **React 18** - UI Framework
- **TypeScript** - Type Safety
- **Vite** - Build Tool & Dev Server
- **TailwindCSS** - Styling
- **TanStack Query (React Query v5)** - State Management & Data Fetching
- **React Router** - Routing
- **Lucide React** - Icons
- **Axios** - HTTP Client

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Struktur

```
src/
├── components/       # UI Components
│   └── Layout.tsx   # Main Layout
├── lib/             # Utilities & API
│   ├── api.ts       # Axios Instance
│   ├── types.ts     # TypeScript Types
│   └── utils.ts     # Helper Functions
├── pages/           # Page Components
│   ├── Dashboard.tsx
│   ├── TracePage.tsx
│   ├── TraceResultPage.tsx
│   ├── AddressAnalysisPage.tsx
│   └── AIAgentPage.tsx
├── App.tsx          # App Entry
├── main.tsx         # React Entry
└── index.css        # Global Styles
```

## Features

### Dashboard
- Übersicht über Plattform-Features
- Statistiken (Placeholder)
- Quick-Links zu Tools

### Transaction Tracing
- Interaktives Formular für Trace-Requests
- Konfiguration von Taint-Modellen (FIFO, Proportional, Haircut)
- Max Depth & Node Limits
- Direction (Forward, Backward, Both)

### AI Agent
- Chat-Interface für forensische Anfragen
- LangChain-gestützte Analyse
- Beispiel-Queries
- Konversations-History

### Address Analysis
- Placeholder für ML-basierte Risikobewertung (Phase 1)

## Environment Variables

```env
VITE_API_URL=http://localhost:8000
VITE_POLICY_EDITOR_DEBOUNCE_MS=250 # Optional: Debounce für Policy-Editor (ms)
```

## Monaco Editor (Policy Manager)

- **Ort**: `src/features/alerts/PolicyManager.tsx`
- **Funktionen**:
  - JSON‑Editing mit Syntax‑Highlighting (Regeln/Events)
  - Live‑Validierung (Regeln via Schema, Events = JSON‑Array)
  - Inline‑Fehlermarker (Parse/AJV)
  - Shortcuts: Formatieren `Cmd/Ctrl+Shift+F`, Minimieren `Cmd/Ctrl+M`
  - Auto‑Format bei Fokusverlust (Blur)
  - Persistenz: Cursor/Scroll, Diff‑State, Entwürfe
- **Hinweise**:
  - Hinweise unter dem Editor per Toolbar‑Toggle ein/ausblendbar
  - Debounce steuerbar via `VITE_POLICY_EDITOR_DEBOUNCE_MS`

## API Integration

Alle API-Calls nutzen React Query für:
- Automatisches Caching
- Loading States
- Error Handling
- Request Deduplication

Beispiel:
```typescript
import { useMutation } from '@tanstack/react-query'
import api from '@/lib/api'

const mutation = useMutation({
  mutationFn: (data) => api.post('/api/v1/trace/start', data),
  onSuccess: (data) => console.log(data),
})
```

## Utilities

### formatAddress()
Kürzt Ethereum-Adressen: `0x1234...5678`

### formatEther()
Konvertiert Wei zu Ether mit Formatierung

### getRiskColor()
Gibt Tailwind-Klassen basierend auf Risk Score zurück

### isValidAddress()
Validiert Ethereum-Adresse

Siehe `src/lib/utils.ts` für alle Utilities.

## Phase 0 (PoC) Status

✅ **Implementiert:**
- Dashboard mit Feature-Übersicht
- Transaction Tracing Form
- AI Agent Chat Interface
- API Integration
- Responsive Design

🚧 **TODO für Phase 1:**
- Graph-Visualisierung (D3.js/Cytoscape)
- Trace-Results-Anzeige
- Address-Risk-Dashboard
- Real-Time Updates (WebSockets)
- Dark Mode
- Export-Funktionen (PDF/CSV)
