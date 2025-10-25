# Frontend Test Suite

## 📁 Struktur

```
tests/
├── unit/                           # Vitest Unit-Tests
│   ├── components/                 # Component-Tests
│   └── utils/                      # Utility-Tests
├── integration/                    # Vitest Integration-Tests
│   ├── ai-agent-stream.spec.tsx   # AI-Agent SSE-Integration
│   ├── patterns-page.spec.tsx     # Patterns-Page mit API
│   └── patterns-buttons.spec.tsx  # Pattern-Buttons-Logik
└── e2e/                            # Playwright E2E-Tests
    ├── chat-widget.spec.ts         # Chat-Widget-Workflows
    ├── investigator-deeplink.spec.ts  # Deep-Links
    ├── consent/                    # Consent-Management
    │   ├── banner.spec.ts
    │   ├── cross-tab.spec.ts
    │   └── preferences.spec.ts
    ├── health/                     # Health-Checks
    │   └── healthz.spec.ts
    ├── metrics/                    # Web-Vitals
    │   └── webvitals.spec.ts
    └── navigation/                 # Navigation-Tests
        └── smoke.spec.ts
```

## 🎯 Test-Typen

### Unit-Tests (Vitest)
- **Zweck**: Isolierte Component/Function-Tests
- **Framework**: Vitest + @testing-library/react
- **Geschwindigkeit**: Sehr schnell
- **Beispiel**:
```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### Integration-Tests (Vitest)
- **Zweck**: Component + API/State-Integration
- **Framework**: Vitest + @testing-library/react + React Query
- **Mock**: API-Calls, EventSource
- **Beispiel**: `integration/ai-agent-stream.spec.tsx`

### E2E-Tests (Playwright)
- **Zweck**: Vollständige User-Journeys im Browser
- **Framework**: Playwright
- **Browser**: Chromium, Firefox, WebKit
- **Beispiel**: `e2e/chat-widget.spec.ts`

## 🚀 Tests ausführen

```bash
# Alle Tests
npm run test                # Vitest (Unit + Integration)
npm run test:e2e            # Playwright (E2E)

# Vitest mit UI
npm run test:ui

# Playwright mit UI
npm run test:e2e:ui

# Watch-Mode
npm run test -- --watch

# Coverage
npm run test -- --coverage

# Spezifischer Test
npm run test -- ai-agent-stream.spec.tsx
npx playwright test chat-widget.spec.ts

# Mit Makefile (von Root)
make test-frontend          # Alle
make test-frontend-unit     # Nur Vitest
make test-frontend-e2e      # Nur Playwright
```

## 📝 Test-Konventionen

### Datei-Benennung

- **Unit/Integration (Vitest)**: `*.spec.tsx` oder `*.spec.ts`
- **E2E (Playwright)**: `*.spec.ts` (nur in `tests/e2e/`)

### Test-Struktur

```typescript
describe('Feature', () => {
  beforeEach(() => {
    // Setup
  })

  it('should do something', () => {
    // Arrange
    const user = userEvent.setup()
    
    // Act
    render(<Component />)
    await user.click(screen.getByRole('button'))
    
    // Assert
    expect(screen.getByText('Result')).toBeInTheDocument()
  })
})
```

### Playwright E2E

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should navigate correctly', async ({ page }) => {
    await page.click('text=Login')
    await expect(page).toHaveURL('/login')
  })
})
```

## 🎭 Playwright-Konfiguration

Siehe `playwright.config.ts`:
- **Test-Verzeichnis**: `tests/e2e/`
- **Browser**: Chromium, Firefox, WebKit
- **Screenshots**: Bei Fehler
- **Videos**: Bei Fehler
- **Retries**: 2x in CI

## 🧪 Mocking

### API-Mocking (Vitest)

```typescript
import { vi } from 'vitest'

vi.mock('@/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  }
}))

const { api } = await import('@/lib/api')
(api.get as any).mockResolvedValue({ data: mockData })
```

### EventSource-Mocking

```typescript
class MockEventSource {
  url: string
  listeners: Record<string, Function[]> = {}
  
  addEventListener(type: string, cb: Function) {
    this.listeners[type] ||= []
    this.listeners[type].push(cb)
  }
  
  emit(type: string, data: any) {
    const event = { data: JSON.stringify(data) }
    this.listeners[type]?.forEach(cb => cb(event))
  }
}

vi.stubGlobal('EventSource', MockEventSource)
```

## 📊 Coverage

Coverage-Ziele:
- **Components**: ≥70%
- **Utils**: ≥80%
- **Critical Paths**: ≥90%

Report generieren:
```bash
npm run test -- --coverage
open coverage/index.html
```

## 🐛 Debugging

### Vitest
```bash
# Mit UI
npm run test:ui

# Mit Console-Output
npm run test -- --reporter=verbose

# Einzelner Test
npm run test -- -t "test name pattern"
```

### Playwright
```bash
# Mit Inspector
npx playwright test --debug

# Mit sichtbarem Browser
npx playwright test --headed

# Mit UI
npm run test:e2e:ui

# Trace Viewer
npx playwright show-trace test-results/.../trace.zip
```

## 🔄 CI/CD

Tests in GitHub Actions:
```yaml
- name: Frontend Tests
  run: |
    cd frontend
    npm run test
    npm run build
    npm run test:e2e
```

## 📚 Best Practices

1. **User-Event über fireEvent**: `userEvent.click()` statt `fireEvent.click()`
2. **Role-basierte Queries**: `getByRole('button')` statt `getByTestId()`
3. **Async-Handling**: `await waitFor()` für asynchrone Updates
4. **Clean-Queries**: `screen.getByText(/pattern/i)` für flexible Matches
5. **Isolation**: Jeder Test sollte unabhängig laufen
6. **Setup/Teardown**: `beforeEach`/`afterEach` für wiederholbaren Setup
7. **Descriptive Names**: Test-Namen sollten Intent beschreiben

## 📚 Weitere Infos

- Siehe `/TESTING_GUIDE.md` für vollständige Dokumentation
- Siehe `setup.ts` für globale Test-Setup
- Siehe `playwright.config.ts` für E2E-Konfiguration
