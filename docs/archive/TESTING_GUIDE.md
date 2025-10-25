# Testing Guide - Blockchain Forensics Platform

## 📋 Übersicht

Dieses Projekt verwendet eine **state-of-the-art Test-Struktur** mit klarer Trennung zwischen:
- **Unit-Tests**: Schnell, isoliert, keine externen Dependencies
- **Integration-Tests**: Mit DB, Redis, APIs
- **E2E-Tests**: Vollständige User-Journeys
- **Security-Tests**: OWASP, Penetration, Dependency-Checks

## 🏗️ Test-Struktur

### Backend (Python/pytest)

```
backend/tests/
├── unit/                           # Unit-Tests (schnell, isoliert)
│   ├── models/                     # Model-Tests
│   └── services/                   # Service-Tests
├── integration/                    # Integration-Tests
│   ├── api/                        # API-Endpoint-Tests
│   │   ├── test_agent_consolidated.py      # AI-Agent-Tests
│   │   ├── test_alerts_consolidated.py     # Alert-Engine-Tests
│   │   ├── test_risk_consolidated.py       # Risk-Engine-Tests
│   │   ├── test_orgs_api.py                # Organizations
│   │   ├── test_chat_api.py                # Chat
│   │   └── ...
│   ├── adapters/                   # Chain-Adapter-Tests
│   │   ├── test_bitcoin_adapter.py
│   │   ├── test_solana_adapter.py
│   │   └── test_l2_adapters.py
│   └── workers/                    # Worker-Tests
│       └── test_integration_workers.py
├── e2e/                            # End-to-End-Tests
│   └── test_enterprise_integration.py
├── security/                       # Security-Tests
│   ├── test_api_security.py
│   ├── test_authentication.py
│   ├── test_crypto_security.py
│   ├── test_sql_injection.py
│   └── test_xss_csrf.py
└── fixtures/                       # Shared Test-Fixtures
```

### Frontend (TypeScript/Vitest/Playwright)

```
frontend/tests/
├── unit/                           # Vitest Unit-Tests
│   ├── components/                 # Component-Tests
│   └── utils/                      # Utility-Tests
├── integration/                    # Vitest Integration-Tests
│   ├── ai-agent-stream.spec.tsx   # AI-Agent-Integration
│   ├── patterns-page.spec.tsx     # Patterns-Page
│   └── patterns-buttons.spec.tsx  # Patterns-Buttons
└── e2e/                            # Playwright E2E-Tests
    ├── chat-widget.spec.ts         # Chat-Widget
    ├── investigator-deeplink.spec.ts
    ├── consent/                    # Consent-Management
    ├── health/                     # Health-Checks
    ├── metrics/                    # Web-Vitals
    └── navigation/                 # Navigation-Tests
```

## 🚀 Tests ausführen

### Alle Tests (Master-Script)

```bash
# Alle Tests mit einem Befehl
./run-all-tests.sh

# Mit Security-Scans
RUN_SECURITY_SCANS=true ./run-all-tests.sh
```

### Backend-Tests

```bash
cd backend

# Alle Tests
pytest tests/ -v

# Nur Unit-Tests (schnell)
pytest tests/unit -v -m unit

# Nur Integration-Tests
pytest tests/integration -v -m integration

# Nur Security-Tests
pytest tests/security -v -m security

# Spezifische Kategorien
pytest tests -v -m agent          # AI-Agent-Tests
pytest tests -v -m alert          # Alert-Engine-Tests
pytest tests -v -m risk           # Risk-Engine-Tests
pytest tests -v -m adapter        # Chain-Adapter-Tests
pytest tests -v -m bridge         # Bridge-Detection-Tests
pytest tests -v -m clustering     # Clustering-Tests

# Mit Coverage
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Langsame Tests überspringen
pytest tests/ -v -m "not slow"

# Nur fehlgeschlagene Tests wiederholen
pytest tests/ -v --lf
```

### Frontend-Tests

```bash
cd frontend

# Vitest Unit & Integration Tests
npm run test                # Einmalig
npm run test:ui             # Mit UI

# Playwright E2E Tests
npm run test:e2e            # Alle Browser
npm run test:e2e:ui         # Mit UI

# Spezifische Tests
npm run test -- ai-agent-stream.spec.tsx
npx playwright test chat-widget.spec.ts
```

## 🏷️ Test-Marker (Backend)

Pytest-Marker für Filterung und Organisation:

| Marker | Beschreibung | Beispiel |
|--------|--------------|----------|
| `unit` | Schnelle Unit-Tests ohne Dependencies | `@pytest.mark.unit` |
| `integration` | Tests mit DB, Redis, etc. | `@pytest.mark.integration` |
| `e2e` | End-to-End voller Stack | `@pytest.mark.e2e` |
| `slow` | Tests > 5 Sekunden | `@pytest.mark.slow` |
| `security` | Security-spezifische Tests | `@pytest.mark.security` |
| `api` | API-Endpoint-Tests | `@pytest.mark.api` |
| `adapter` | Chain-Adapter-Tests | `@pytest.mark.adapter` |
| `agent` | AI-Agent-Tests | `@pytest.mark.agent` |
| `alert` | Alert-Engine-Tests | `@pytest.mark.alert` |
| `risk` | Risk-Engine-Tests | `@pytest.mark.risk` |
| `bridge` | Bridge-Detection-Tests | `@pytest.mark.bridge` |
| `clustering` | Clustering/ML-Tests | `@pytest.mark.clustering` |

Verwendung:
```python
import pytest

@pytest.mark.unit
def test_my_function():
    assert True

@pytest.mark.integration
@pytest.mark.api
def test_api_endpoint():
    assert True

@pytest.mark.slow
@pytest.mark.e2e
def test_full_workflow():
    assert True
```

## 📊 Coverage-Ziele

- **Backend**: ≥80% Line Coverage
- **Frontend**: ≥70% Line Coverage
- **Kritische Module** (Security, Auth): ≥90%

Coverage-Reports:
```bash
# Backend
cd backend
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm run test -- --coverage
open coverage/index.html
```

## 🔒 Security-Tests

```bash
# Vollständiger Security-Audit
make security-scan

# Einzelne Tools
cd backend
bandit -r app/ -f txt              # SAST
safety check                       # Dependencies
semgrep --config=.semgrep.yml      # Pattern-basiert
detect-secrets scan --all-files    # Secrets
```

## 🐛 Debugging

### Backend

```python
# Mit pdb debuggen
pytest tests/test_file.py -v -s --pdb

# Nur fehlgeschlagene Tests
pytest tests/ --lf

# Mit ausführlichem Output
pytest tests/ -vv --tb=long

# Specific test function
pytest tests/test_file.py::test_function_name -v
```

### Frontend

```bash
# Vitest Debugging
npm run test:ui                    # Mit Browser UI

# Playwright Debugging
npx playwright test --debug        # Mit Inspector
npx playwright test --headed       # Mit sichtbarem Browser
npx playwright test --ui           # Mit Test-UI
```

## 📝 Test-Best-Practices

### 1. Test-Benennung

```python
# ✅ Gut: Beschreibend und klar
def test_user_can_login_with_valid_credentials():
    pass

def test_api_returns_404_for_nonexistent_resource():
    pass

# ❌ Schlecht: Unklar
def test_1():
    pass

def test_stuff():
    pass
```

### 2. Arrange-Act-Assert Pattern

```python
def test_risk_score_calculation():
    # Arrange: Setup
    address = "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"
    expected_score = 0.75
    
    # Act: Execute
    result = calculate_risk_score(address)
    
    # Assert: Verify
    assert result == expected_score
```

### 3. Fixtures verwenden

```python
@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def sample_address():
    return "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"

def test_with_fixtures(test_client, sample_address):
    response = test_client.get(f"/api/v1/risk?address={sample_address}")
    assert response.status_code == 200
```

### 4. Parametrisierte Tests

```python
@pytest.mark.parametrize("address,expected_valid", [
    ("0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4", True),
    ("invalid", False),
    ("0x123", False),
])
def test_address_validation(address, expected_valid):
    assert is_valid_address(address) == expected_valid
```

### 5. Mocking externe Services

```python
from unittest.mock import patch, MagicMock

@patch('app.services.external_api.fetch_data')
def test_with_mocked_api(mock_fetch):
    mock_fetch.return_value = {"result": "mocked"}
    result = my_function_that_uses_api()
    assert result == {"result": "mocked"}
    mock_fetch.assert_called_once()
```

## 🔄 CI/CD Integration

Tests werden automatisch in GitHub Actions ausgeführt:

```yaml
# .github/workflows/ci-cd.yml
- name: Run Backend Tests
  run: |
    cd backend
    pytest tests/ -v --cov=app --cov-report=xml

- name: Run Frontend Tests
  run: |
    cd frontend
    npm run test
    npm run test:e2e
```

## 📚 Konsolidierte Tests

Folgende Tests wurden konsolidiert für bessere Wartbarkeit:

### AI-Agent-Tests → `test_agent_consolidated.py`
Vereint: `test_agent_api_tools.py`, `test_agent_health.py`, `test_agent_tools_api.py`, etc.

### Alert-Tests → `test_alerts_consolidated.py`
Vereint: `test_alert_engine_suppression.py`, `test_alerts_kpis_endpoint.py`, etc.

### Risk-Tests → `test_risk_consolidated.py`
Vereint: `test_risk_api.py`, `test_risk_weights_api.py`, `test_rule_engine.py`, etc.

## ❓ Troubleshooting

### "No module named 'app'"
```bash
# Sicherstellen, dass PYTHONPATH gesetzt ist
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### Playwright-Timeout
```bash
# Timeout erhöhen
npx playwright test --timeout=60000
```

### Coverage zu niedrig
```bash
# Detaillierte Coverage-Analyse
pytest tests/ --cov=app --cov-report=term-missing
# Zeigt fehlende Zeilen
```

## 🎯 Quick Reference

```bash
# Schnelltest (nur Unit)
cd backend && pytest tests/unit -v -m unit

# Vollständiger Test mit Coverage
./run-all-tests.sh

# Nur geänderte Tests
cd backend && pytest tests/ -v --testmon

# Frontend Watch-Mode
cd frontend && npm run test -- --watch

# E2E mit UI
cd frontend && npm run test:e2e:ui
```

## 📞 Support

Bei Fragen oder Problemen:
1. Siehe `TEST_ANALYSIS.md` für detaillierte Struktur-Analyse
2. Prüfe CI-Logs in GitHub Actions
3. Dokumentiere neue Tests gemäß diesem Guide
