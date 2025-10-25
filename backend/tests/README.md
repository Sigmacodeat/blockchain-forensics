# Backend Test Suite

## 📁 Struktur

```
tests/
├── unit/                    # Unit-Tests (schnell, isoliert)
│   ├── models/              # Model-Tests
│   └── services/            # Service-Tests
├── integration/             # Integration-Tests (mit DB, Redis, etc.)
│   ├── api/                 # API-Endpoint-Tests
│   │   ├── test_agent_consolidated.py       # AI-Agent (konsolidiert)
│   │   ├── test_alerts_consolidated.py      # Alerts (konsolidiert)
│   │   ├── test_risk_consolidated.py        # Risk (konsolidiert)
│   │   └── ...              # Weitere API-Tests
│   ├── adapters/            # Chain-Adapter-Tests
│   │   ├── test_bitcoin_adapter.py
│   │   ├── test_solana_adapter.py
│   │   └── test_l2_adapters.py
│   └── workers/             # Worker-Tests
│       └── test_integration_workers.py
├── e2e/                     # End-to-End-Tests
│   └── test_enterprise_integration.py
├── security/                # Security-Tests
│   ├── test_api_security.py
│   ├── test_authentication.py
│   ├── test_crypto_security.py
│   ├── test_sql_injection.py
│   └── test_xss_csrf.py
└── fixtures/                # Shared Test-Fixtures
```

## 🏷️ Test-Marker

Verwende pytest-Marker für bessere Organisation:

```python
import pytest

@pytest.mark.unit              # Unit-Test (schnell)
@pytest.mark.integration       # Integration-Test (DB/Redis)
@pytest.mark.e2e              # End-to-End-Test
@pytest.mark.slow             # Langsamer Test (>5s)
@pytest.mark.security         # Security-Test
@pytest.mark.api              # API-Test
@pytest.mark.adapter          # Chain-Adapter-Test
@pytest.mark.agent            # AI-Agent-Test
@pytest.mark.alert            # Alert-Engine-Test
@pytest.mark.risk             # Risk-Engine-Test
@pytest.mark.bridge           # Bridge-Detection-Test
@pytest.mark.clustering       # Clustering/ML-Test
```

## 🚀 Tests ausführen

```bash
# Alle Tests
pytest tests/ -v

# Nur Unit-Tests (schnell)
pytest tests/unit -v -m unit

# Nur Integration-Tests
pytest tests/integration -v -m integration

# Nur Security-Tests
pytest tests/security -v -m security

# Spezifische Kategorie
pytest tests/ -v -m agent          # AI-Agent
pytest tests/ -v -m alert          # Alerts
pytest tests/ -v -m risk           # Risk
pytest tests/ -v -m adapter        # Adapters
pytest tests/ -v -m bridge         # Bridges
pytest tests/ -v -m clustering     # Clustering

# Mit Coverage
pytest tests/ -v --cov=app --cov-report=html

# Schnelle Tests (keine slow)
pytest tests/ -v -m "not slow"

# Fehlgeschlagene Tests wiederholen
pytest tests/ -v --lf

# Mit Makefile
make test-backend              # Alle Backend-Tests
make test-backend-unit         # Nur Unit
make test-backend-integration  # Nur Integration
make test-agent                # Nur Agent-Tests
```

## 📝 Konventionen

### Test-Benennung

```python
# ✅ Gut
def test_user_login_with_valid_credentials():
    pass

def test_api_returns_404_for_nonexistent_user():
    pass

# ❌ Schlecht
def test_1():
    pass

def test_stuff():
    pass
```

### Arrange-Act-Assert

```python
def test_calculate_risk_score():
    # Arrange
    address = "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"
    
    # Act
    result = calculate_risk_score(address)
    
    # Assert
    assert result >= 0 and result <= 1
```

### Fixtures

```python
@pytest.fixture
def sample_address():
    return "0x742d35Cc6634C0532925a3b8D807A69F8e4F41d4"

def test_with_fixture(sample_address):
    assert is_valid_address(sample_address)
```

## 📊 Coverage-Ziele

- **Gesamt**: ≥80%
- **Kritische Module** (Security, Auth): ≥90%
- **API-Endpoints**: 100%

## 🔄 Konsolidierte Tests

Folgende Test-Kategorien wurden konsolidiert:

1. **AI-Agent-Tests** → `integration/api/test_agent_consolidated.py`
   - Ursprünglich 9 Dateien
   - Jetzt: Health, Tools, Policy, Simulation, Extraction

2. **Alert-Tests** → `integration/api/test_alerts_consolidated.py`
   - Ursprünglich 9 Dateien
   - Jetzt: API, Rules, Suppressions, KPIs, Monitoring

3. **Risk-Tests** → `integration/api/test_risk_consolidated.py`
   - Ursprünglich 7 Dateien
   - Jetzt: API, Weights, Admin, Rules Engine

## 🐛 Debugging

```bash
# Mit pdb
pytest tests/test_file.py -v -s --pdb

# Verbose Output
pytest tests/ -vv --tb=long

# Einzelner Test
pytest tests/test_file.py::test_function_name -v
```

## 📚 Weitere Infos

Siehe `/TESTING_GUIDE.md` für vollständige Dokumentation.
