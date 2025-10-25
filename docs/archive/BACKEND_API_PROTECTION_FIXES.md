# 🔒 BACKEND API PROTECTION FIXES - IMPLEMENTIERUNGSPLAN

## KRITISCHE FIXES (SOFORT):

### 1. TRACE API SICHERN

**File**: `backend/app/api/v1/trace.py`

**Alle Endpoints mit require_plan() schützen:**

```python
from app.auth.dependencies import require_plan

# Community+ (Kostenlos)
@router.post("/trace", status_code=201)
async def create_trace(
    request: TraceRequestAPI,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_plan('community'))  # ✅ FIX
):
    # Plan aus Token, nicht aus Redis!
    plan_id = current_user.get('plan', 'community')
    tenant_id = current_user["user_id"]
    # Credits-Check als zusätzliche Sicherheit
    allowed = await check_and_consume_credits(tenant_id, plan_id, 10)
    # ... rest of logic

# Pro+ Features
@router.post("/trace/advanced", status_code=201)
async def create_advanced_trace(
    request: AdvancedTraceRequest,
    current_user: dict = Depends(require_plan('pro'))  # ✅ FIX
):
    # ... logic
```

---

### 2. GRAPH ANALYTICS SICHERN

**File**: `backend/app/api/v1/graph_analytics.py`

```python
from app.auth.dependencies import require_plan

# Pro+ Features
@router.post("/communities/detect")
async def detect_communities(
    request: CommunityDetectionRequest,
    current_user: dict = Depends(require_plan('pro'))  # ✅ FIX
):
    plan_id = current_user.get('plan', 'community')
    tenant_id = current_user["user_id"]
    allowed = await check_and_consume_credits(tenant_id, plan_id, 5)
    # ... logic

@router.post("/centrality/calculate")
async def calculate_centrality(
    request: CentralityRequest,
    current_user: dict = Depends(require_plan('pro'))  # ✅ FIX
):
    # ... logic

@router.post("/patterns/circles")
async def detect_circles(
    request: CircleDetectionRequest,
    current_user: dict = Depends(require_plan('pro'))  # ✅ FIX
):
    # ... logic
```

---

### 3. CASES API MIT ORG_ID SICHERN

**File**: `backend/app/api/v1/cases.py`

```python
from app.auth.dependencies import get_current_user, require_plan

# Alle User können Cases sehen (Community+)
@router.get("/cases")
async def list_cases(
    current_user: dict = Depends(get_current_user)
):
    org_id = current_user.get('org_id')
    user_id = current_user["user_id"]
    
    # ✅ FIX: Org-Filtering
    query = """
        SELECT * FROM cases 
        WHERE (org_id = :org_id OR created_by = :user_id)
        ORDER BY created_at DESC
    """
    cases = await db.fetch_all(query, {"org_id": org_id, "user_id": user_id})
    return cases

# Case Details mit Org-Check
@router.get("/cases/{case_id}")
async def get_case(
    case_id: str,
    current_user: dict = Depends(get_current_user)
):
    org_id = current_user.get('org_id')
    user_id = current_user["user_id"]
    
    # ✅ FIX: Org-Validierung
    query = """
        SELECT * FROM cases 
        WHERE id = :case_id 
        AND (org_id = :org_id OR created_by = :user_id)
    """
    case = await db.fetch_one(query, {
        "case_id": case_id, 
        "org_id": org_id, 
        "user_id": user_id
    })
    
    if not case:
        raise HTTPException(404, "Case not found")
    
    return case

# CREATE benötigt Community+ (oder Starter+?)
@router.post("/cases")
async def create_case(
    case_data: CaseCreate,
    current_user: dict = Depends(require_plan('community'))  # ✅ FIX
):
    org_id = current_user.get('org_id')
    user_id = current_user["user_id"]
    
    # ✅ FIX: Org-ID setzen
    case = {
        **case_data.dict(),
        "org_id": org_id,
        "created_by": user_id
    }
    # ... insert logic
```

---

### 4. WALLET SCANNER SICHERN

**File**: `backend/app/api/v1/wallet_scanner.py`

```python
from app.auth.dependencies import require_plan

# Pro+ Feature
@router.post("/wallet-scanner/scan/seed-phrase")
async def scan_seed_phrase(
    request: SeedPhraseScanRequest,
    current_user: dict = Depends(require_plan('pro'))  # ✅ FIX
):
    # ... logic

@router.post("/wallet-scanner/scan/addresses")
async def scan_addresses(
    request: AddressesScanRequest,
    current_user: dict = Depends(require_plan('pro'))  # ✅ FIX
):
    # ... logic
```

---

### 5. AI AGENT SICHERN

**File**: `backend/app/api/v1/agent.py` oder `ai_assistant.py`

```python
from app.auth.dependencies import require_plan

# Plus+ Feature
@router.post("/ai-agent/chat")
async def chat_with_agent(
    request: ChatRequest,
    current_user: dict = Depends(require_plan('plus'))  # ✅ FIX
):
    # ... logic

@router.get("/ai-agent/tools")
async def list_tools(
    current_user: dict = Depends(require_plan('plus'))  # ✅ FIX
):
    # ... logic
```

---

### 6. ADMIN ROUTEN HÄRTEN

**Alle Admin-Endpoints prüfen:**

```python
from app.auth.dependencies import require_admin

# ✅ Korrekt
@router.get("/admin/analytics")
async def get_analytics(current_user: dict = Depends(require_admin)):
    # ... logic

# ❌ Fixieren
@router.get("/admin/users")
async def list_users(current_user: dict = Depends(require_admin)):  # ✅ FIX
    # ... logic

@router.get("/orgs")
async def list_orgs(current_user: dict = Depends(require_admin)):  # ✅ FIX
    # ... logic
```

---

## JWT TOKEN ERWEITERN

**File**: `backend/app/auth/jwt.py`

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TokenData:
    user_id: str
    email: str
    role: UserRole
    plan: str  # ✅ FIX: Nicht mehr Optional!
    org_id: Optional[str] = None  # ✅ NEU: Für Multi-Tenancy
    features: List[str] = field(default_factory=list)
    exp: Optional[int] = None

def create_token(user: dict) -> str:
    """JWT Token mit allen User-Daten"""
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "plan": user.get("plan", "community"),  # ✅ FIX: Default!
        "org_id": user.get("org_id"),  # ✅ NEU!
        "features": user.get("features", []),
        "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

**Update in dependencies.py:**

```python
async def get_current_user_strict(credentials) -> dict:
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(401, "Invalid token")
    
    return {
        "user_id": token_data.user_id,
        "email": token_data.email,
        "role": token_data.role.value,
        "plan": token_data.plan,  # ✅ FIX: Immer vorhanden!
        "org_id": token_data.org_id,  # ✅ NEU!
        "features": token_data.features
    }
```

---

## ORG_ID HELPER FUNCTION

**File**: `backend/app/utils/auth_helpers.py` (neu)

```python
from fastapi import HTTPException

def require_org_ownership(resource_org_id: str, user_org_id: str):
    """
    Prüft ob User Zugriff auf Resource hat (gleiche Org)
    
    Args:
        resource_org_id: Org-ID der Resource
        user_org_id: Org-ID des Users
    
    Raises:
        HTTPException: 403 wenn Orgs nicht übereinstimmen
    """
    if not user_org_id:
        raise HTTPException(403, "User has no organization")
    
    if resource_org_id != user_org_id:
        raise HTTPException(403, "Access denied: wrong organization")

def get_org_filter_clause(user_org_id: str, user_id: str) -> dict:
    """
    Generiert SQL-Filter für Org-Isolation
    
    Returns:
        {"org_id": str, "user_id": str} für WHERE-Clause
    """
    return {
        "org_id": user_org_id,
        "user_id": user_id
    }
```

**Verwendung:**

```python
from app.utils.auth_helpers import require_org_ownership

@router.put("/cases/{case_id}")
async def update_case(
    case_id: str,
    update_data: CaseUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Hole Case
    case = await db.fetch_one("SELECT * FROM cases WHERE id = :id", {"id": case_id})
    if not case:
        raise HTTPException(404, "Case not found")
    
    # ✅ Org-Check
    require_org_ownership(case['org_id'], current_user.get('org_id'))
    
    # Update erlaubt
    # ... update logic
```

---

## TESTING PLAN

### Unit Tests:

```python
# tests/test_auth_protection.py
import pytest
from fastapi import HTTPException

def test_require_plan_blocks_lower_plans():
    """Community User kann nicht auf Pro-Features zugreifen"""
    user = {"user_id": "test", "role": "viewer", "plan": "community"}
    
    with pytest.raises(HTTPException) as exc:
        await require_plan('pro')(user)
    
    assert exc.value.status_code == 403
    assert "Plan upgrade required" in str(exc.value.detail)

def test_require_plan_allows_higher_plans():
    """Business User kann auf Pro-Features zugreifen"""
    user = {"user_id": "test", "role": "viewer", "plan": "business"}
    
    # Sollte funktionieren
    result = await require_plan('pro')(user)
    assert result == user

def test_org_ownership_check():
    """User kann nur eigene Org-Resources zugreifen"""
    with pytest.raises(HTTPException) as exc:
        require_org_ownership("org_123", "org_456")
    
    assert exc.value.status_code == 403
    assert "wrong organization" in str(exc.value.detail)
```

### Integration Tests:

```python
# tests/test_api_protection_integration.py
def test_trace_requires_community_plan(client):
    """Trace-Endpoint prüft Plan"""
    # User ohne Plan (sollte blocked werden)
    token = create_test_token(user_id="test", plan=None)
    
    response = client.post(
        "/api/v1/trace",
        json={"source_address": "0x123..."},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "Plan upgrade required" in response.json()["detail"]

def test_investigator_requires_pro_plan(client):
    """Graph-Analysen brauchen Pro-Plan"""
    token = create_test_token(user_id="test", plan="community")
    
    response = client.post(
        "/api/v1/graph-analytics/communities/detect",
        json={"algorithm": "louvain"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
```

---

## DEPLOYMENT CHECKLIST

- [ ] 1. JWT Token erweitern (plan + org_id)
- [ ] 2. Alle User-Tokens neu generieren (einmaliger Login erforderlich)
- [ ] 3. require_plan() zu allen kritischen Endpoints hinzufügen
- [ ] 4. org_id Validierung zu allen Multi-Tenant-Endpoints
- [ ] 5. Admin-Routen mit require_admin schützen
- [ ] 6. Tests schreiben und ausführen
- [ ] 7. Staging-Deployment testen
- [ ] 8. Audit-Logging aktivieren
- [ ] 9. Production-Deployment
- [ ] 10. Monitoring aktivieren (Plan-Check-Failures tracken)

---

## ROLLBACK PLAN

Falls Probleme auftreten:

1. **JWT-Schema Änderung**: Tokens mit altem Schema noch 24h akzeptieren
2. **API-Protection**: Feature-Flag für neue Guards (`ENABLE_PLAN_GUARDS=false`)
3. **Monitoring**: Fehlerrate tracken, bei >1% automatisch rollback

**Geschätzte Implementierungszeit**: 2-3 Tage
**Risiko**: Mittel (breaking change bei JWT)
**Business-Impact**: HOCH (verhindert Missbrauch, schützt Revenue)
