# 🔒 INLINE-CHAT SECURITY - IMPLEMENTATION STATUS

**Datum**: 19. Oktober 2025, 20:10 Uhr  
**Status**: 🟡 **IN PROGRESS** (15% Complete)

---

## ✅ BEREITS IMPLEMENTIERT (15%)

### 1. **Audit Service** - ✅ COMPLETE
- **File**: `backend/app/services/audit_service.py` (NEU, 250 Zeilen)
- **Features**:
  - Komplett audit_logs Tabelle mit Indexes
  - log_action() für beliebige Events
  - log_tool_call() für AI-Tool-Executions
  - log_download() für Report-Downloads
  - log_case_action() für Case-Management
  - get_user_audit_trail() für GDPR-Compliance
  - Automatic sanitization (Passwords, Keys entfernt)
- **Status**: ✅ **PRODUKTIONSREIF**

### 2. **Rate Limiter** - ✅ EXISTS (Erweitern nötig)
- **File**: `backend/app/middleware/rate_limiter.py` (EXISTIERT)
- **Features**:
  - Plan-basierte Limits (Community: 10/min, Pro: 100/min, etc.)
  - Redis-backed mit In-Memory-Fallback
  - 429 Responses mit Retry-After Headers
  - Audit-Logging bei Limit-Überschreitung
- **Status**: ✅ **PRODUKTIONSREIF** (nur Tool-spezifische Rate-Limits fehlen)

### 3. **Input Validators** - ⚠️ PARTIAL
- **File**: `backend/app/utils/validators.py` (EXISTIERT, basic)
- **Vorhandene Functions**:
  - `is_valid_address()` für ETH/BTC/SOL
  - `normalize_address()` für Case-Handling
- **NEU HINZUGEFÜGT**: `backend/app/utils/security.py` (NEU, 150 Zeilen)
  - `validate_eth_address()` - Ethereum 0x...
  - `validate_string_length()` - Min/Max Länge
  - `sanitize_html()` - XSS-Protection
  - `validate_bitcoin_address()` - BTC P2PKH/P2SH/Bech32
  - `validate_url()` - URL-Format mit Scheme-Check
  - `sanitize_filename()` - Path-Traversal-Protection
  - `mask_sensitive_data()` - Email/PII-Masking
- **Status**: ✅ **KOMPLETT** für Phase 1

---

## 🔴 NOCH ZU IMPLEMENTIEREN (85%)

### PHASE 1: KRITISCHE SECURITY (3-4 Tage)

#### 1. **Authentication in Tools** - ⏳ 0% DONE
**Files zu ändern**:
- `backend/app/ai_agents/tools/case_management_tools.py`
- `backend/app/ai_agents/tools/report_generation_tools.py`

**Änderungen**:
```python
# ✅ ADD zu jedem Tool:
@tool("create_case")
async def create_case_tool(
    title: str,
    description: str,
    user_id: str,  # ← HINZUFÜGEN
    ...
):
    # ✅ Validate inputs
    if not validate_string_length(title, 1, 200):
        return {"success": False, "error": "Invalid title"}
    
    # ✅ Sanitize
    title = sanitize_html(title)
    
    # ✅ Check permissions
    user = await get_user(user_id)
    if not user.can_create_cases():
        return {"success": False, "error": "No permission"}
    
    # ✅ Audit log
    await audit_service.log_tool_call(
        tool_name="create_case",
        user_id=user_id,
        args={"title": title, ...},
        success=True
    )
```

**Aufwand**: 2-3 Stunden pro File (Total: 6 Stunden)

---

#### 2. **Authorization für Downloads** - ⏳ 0% DONE
**Files zu ändern**:
- `backend/app/api/v1/reports.py` (Authorization hinzufügen)
- `frontend/src/components/chat/ForensicResultDisplay.tsx` (Auth-Headers)

**Backend-Änderungen**:
```python
@router.get("/trace/{trace_id}/download/{format}")
async def download_trace_report(
    trace_id: str,
    format: str,
    current_user: dict = Depends(get_current_user_strict)  # ← ADD
):
    # ✅ Check ownership
    trace = await get_trace_by_id(trace_id)
    if trace.owner_id != current_user["user_id"]:
        raise HTTPException(403, "Not your trace")
    
    # ✅ Audit log
    await audit_service.log_download(
        user_id=current_user["user_id"],
        resource_type="trace_report",
        resource_id=trace_id,
        format=format
    )
    
    # Generate & return file...
```

**Frontend-Änderungen**:
```typescript
// frontend/src/components/chat/ForensicResultDisplay.tsx
const handleDownload = async (downloadFormat: string) => {
  const token = localStorage.getItem('auth_token')
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,  // ← ADD
      'X-User-ID': getCurrentUserId()
    }
  })
  
  if (response.status === 403) {
    alert('Keine Berechtigung')
    return
  }
}
```

**Aufwand**: 2-3 Stunden

---

#### 3. **Tool-Specific Rate-Limiting** - ⏳ 0% DONE
**New File**: `backend/app/services/tool_rate_limiter.py` (200 Zeilen)

```python
class ToolRateLimiter:
    """Rate limiting for AI tool calls"""
    
    LIMITS = {
        "create_case": {"free": 5, "pro": 50, "plus": 200, "window": 3600},
        "generate_trace_report": {"free": 5, "pro": 50, "plus": 200, "window": 3600},
        "export_case": {"free": 10, "pro": 100, "plus": 500, "window": 3600}
    }
    
    async def check_limit(self, user_id: str, tool_name: str, plan: str) -> tuple[bool, int]:
        """Check if user is within tool-specific limit"""
        limit_config = self.LIMITS.get(tool_name)
        if not limit_config:
            return (True, 0)  # No limit
        
        limit = limit_config.get(plan, 10)
        window = limit_config["window"]
        
        # Check Redis
        key = f"tool_limit:{user_id}:{tool_name}:{int(time.time() // window)}"
        count = await redis_client.incr(key)
        await redis_client.expire(key, window)
        
        return (count <= limit, count)
```

**Integration in Tools**:
```python
@tool("create_case")
async def create_case_tool(..., user_id: str):
    # ✅ Rate limit check
    allowed, count = await tool_rate_limiter.check_limit(
        user_id=user_id,
        tool_name="create_case",
        plan=user.plan
    )
    
    if not allowed:
        return {
            "success": False,
            "error": f"Rate limit exceeded. Max {limit}/hour.",
            "retry_after": 3600
        }
```

**Aufwand**: 4-5 Stunden

---

### PHASE 2: COMPLIANCE & GDPR (2-3 Tage)

#### 4. **GDPR Service** - ⏳ 0% DONE
**New File**: `backend/app/services/gdpr_service.py` (300 Zeilen)

```python
class GDPRService:
    """GDPR Compliance Service"""
    
    async def export_user_data(self, user_id: str) -> bytes:
        """Export all user data (Art. 20)"""
        data = {
            "profile": await get_user(user_id),
            "cases": await get_user_cases(user_id),
            "reports": await get_user_reports(user_id),
            "chat_history": await get_user_chats(user_id),
            "audit_logs": await audit_service.get_user_audit_trail(user_id)
        }
        return json.dumps(data, indent=2).encode()
    
    async def delete_user_data(self, user_id: str):
        """Delete/Anonymize user data (Art. 17)"""
        await anonymize_user_cases(user_id)
        await delete_user_chats(user_id)
        await mark_user_deleted(user_id)
    
    async def anonymize_report(self, report_id: str):
        """Remove PII from report"""
        report = await get_report(report_id)
        report.data = self._pseudonymize_addresses(report.data)
        report.creator_email = "redacted@privacy.local"
        await save_report(report)
```

**API Endpoints**:
```python
@router.post("/gdpr/export")
async def export_my_data(current_user: dict = Depends(get_current_user_strict)):
    data = await gdpr_service.export_user_data(current_user["user_id"])
    return Response(content=data, media_type="application/json")

@router.post("/gdpr/delete")
async def delete_my_data(current_user: dict = Depends(get_current_user_strict)):
    await gdpr_service.delete_user_data(current_user["user_id"])
    return {"success": True}
```

**Aufwand**: 1 Tag (8 Stunden)

---

#### 5. **Data Retention Policies** - ⏳ 0% DONE
**New File**: `backend/app/services/retention_service.py` (200 Zeilen)

```python
class RetentionService:
    """Data retention policy enforcement"""
    
    POLICIES = {
        "chat_messages": timedelta(days=90),
        "reports": timedelta(days=365),
        "audit_logs": timedelta(days=730),  # 2 years
        "cases": timedelta(days=1095)  # 3 years
    }
    
    async def cleanup_expired_data(self):
        """Cleanup expired data (CRON job)"""
        for data_type, retention_period in self.POLICIES.items():
            cutoff = datetime.utcnow() - retention_period
            await self._delete_expired(data_type, cutoff)
```

**CRON Job**:
```python
# backend/app/tasks/retention_cleanup.py
@app.task
async def retention_cleanup_job():
    """Daily cleanup job"""
    await retention_service.cleanup_expired_data()
```

**Aufwand**: 4-5 Stunden

---

### PHASE 3: UX FEATURES (2-3 Tage)

#### 6. **Persistent Report Storage (S3)** - ⏳ 0% DONE
**New File**: `backend/app/services/report_storage_service.py` (300 Zeilen)

```python
class ReportStorageService:
    """S3-based persistent report storage"""
    
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket = settings.REPORTS_BUCKET
    
    async def store_report(
        self,
        report_id: str,
        content: bytes,
        format: str,
        user_id: str
    ) -> str:
        """Store report in S3"""
        key = f"reports/{user_id}/{report_id}.{format}"
        
        # Upload
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ServerSideEncryption='AES256',  # Encrypted at rest
            Metadata={
                'user-id': user_id,
                'report-id': report_id,
                'generated-at': datetime.utcnow().isoformat()
            }
        )
        
        # Generate presigned URL (7 days)
        url = self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=604800
        )
        
        # Store metadata in DB
        await postgres_client.execute(
            "INSERT INTO reports (report_id, user_id, s3_key, url, expires_at) VALUES (...)"
        )
        
        return url
    
    async def get_report_url(self, report_id: str, user_id: str) -> str:
        """Get download URL (regenerate if expired)"""
        # Check DB, regenerate if needed
```

**Integration in Tools**:
```python
@tool("generate_trace_report")
async def generate_trace_report_tool(...):
    # Generate PDF
    pdf_content = await generate_pdf(...)
    
    # ✅ Store persistently
    url = await report_storage.store_report(
        report_id=trace_id,
        content=pdf_content,
        format="pdf",
        user_id=user_id
    )
    
    return {
        "success": True,
        "download_url": url,
        "marker": f"[DOWNLOAD:trace:{trace_id}:pdf]"
    }
```

**Aufwand**: 1 Tag (8 Stunden)

---

#### 7. **Email Notifications** - ⏳ 0% DONE
**New File**: `backend/app/services/email_notification_service.py` (250 Zeilen)

```python
class EmailNotificationService:
    """Email notifications for reports"""
    
    async def send_report_ready_email(
        self,
        user_email: str,
        report_type: str,
        report_id: str,
        download_url: str
    ):
        """Send email when report is ready"""
        message = Mail(
            from_email='reports@blockchain-forensics.ai',
            to_emails=user_email,
            subject=f'Your {report_type.upper()} Report is Ready',
            html_content=self._render_template(
                'report_ready',
                {
                    'report_type': report_type,
                    'report_id': report_id,
                    'download_url': download_url
                }
            )
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        await sg.send(message)
```

**Integration**:
```python
@tool("generate_trace_report")
async def generate_trace_report_tool(..., user_email: str = None):
    # Generate & store report
    url = await report_storage.store_report(...)
    
    # ✅ Send email
    if user_email:
        await email_service.send_report_ready_email(
            user_email=user_email,
            report_type="trace",
            report_id=trace_id,
            download_url=url
        )
```

**Aufwand**: 5-6 Stunden

---

#### 8. **Progress Indicators (WebSocket)** - ⏳ 0% DONE
**New File**: `backend/app/services/progress_tracker.py` (200 Zeilen)

```python
class ProgressTracker:
    """Track and broadcast tool progress"""
    
    async def update_progress(
        self,
        user_id: str,
        tool_name: str,
        progress: int,
        status: str
    ):
        """Broadcast progress to user"""
        await websocket_manager.broadcast_to_user(
            user_id=user_id,
            message={
                "type": "tool_progress",
                "tool": tool_name,
                "progress": progress,
                "status": status
            }
        )
```

**Integration**:
```python
@tool("generate_trace_report")
async def generate_trace_report_tool(...):
    await progress_tracker.update_progress(
        user_id=user_id,
        tool_name="generate_trace_report",
        progress=10,
        status="Fetching trace data..."
    )
    
    trace_data = await get_trace_data(trace_id)
    
    await progress_tracker.update_progress(..., progress=50, status="Generating PDF...")
    
    pdf = await generate_pdf(...)
    
    await progress_tracker.update_progress(..., progress=100, status="Complete!")
```

**Frontend**:
```typescript
// frontend/src/components/chat/InlineChatPanel.tsx
const [toolProgress, setToolProgress] = useState(null)

useEffect(() => {
  const ws = new WebSocket(`${WS_URL}/api/v1/chat/ws`)
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'tool_progress') {
      setToolProgress(data)
    }
  }
}, [])

// Render progress bar
{toolProgress && (
  <ProgressBar progress={toolProgress.progress} status={toolProgress.status} />
)}
```

**Aufwand**: 1 Tag (8 Stunden)

---

#### 9. **Report Preview** - ⏳ 0% DONE
**New Endpoint**: `GET /api/v1/reports/{type}/{id}/preview`

```python
@router.get("/trace/{trace_id}/preview")
async def preview_trace_report(
    trace_id: str,
    current_user: dict = Depends(get_current_user_strict)
):
    """Get report preview (first page/summary)"""
    trace = await get_trace_data(trace_id)
    
    # Check ownership
    if trace.owner_id != current_user["user_id"]:
        raise HTTPException(403)
    
    # Generate summary
    summary = {
        "addresses": len(trace.nodes),
        "transactions": len(trace.edges),
        "risk_score": calculate_avg_risk(trace),
        "thumbnail": await generate_thumbnail(trace)
    }
    
    return summary
```

**Frontend**:
```typescript
const handlePreview = async () => {
  const preview = await fetch(`/api/v1/reports/${type}/${resultId}/preview`)
  setPreviewData(await preview.json())
  setShowPreview(true)
}

// Modal with preview
<Modal>
  <img src={previewData.thumbnail} />
  <Stats summary={previewData.summary} />
</Modal>
```

**Aufwand**: 4-5 Stunden

---

#### 10. **Batch Operations** - ⏳ 0% DONE
**New Tool**: `batch_generate_reports`

```python
@tool("batch_generate_reports")
async def batch_generate_reports_tool(
    case_ids: List[str],
    format: str = "pdf",
    user_id: str = None
) -> Dict[str, Any]:
    """Generate reports for multiple cases"""
    
    if len(case_ids) > 50:
        return {"error": "Max 50 cases per batch"}
    
    results = []
    for case_id in case_ids:
        try:
            result = await generate_case_report(case_id, format, user_id)
            results.append({"case_id": case_id, "success": True, ...})
        except Exception as e:
            results.append({"case_id": case_id, "success": False, "error": str(e)})
    
    # Create ZIP
    zip_url = await create_batch_zip(results, user_id)
    
    return {
        "success": True,
        "total": len(case_ids),
        "succeeded": sum(1 for r in results if r['success']),
        "download_url": zip_url
    }
```

**Aufwand**: 5-6 Stunden

---

## 📊 ÜBERSICHT: WORKLOAD

| Phase | Features | Aufwand | Priorität |
|-------|----------|---------|-----------|
| **Phase 1: Security** | Auth, Authorization, Rate-Limiting, Validation | 2-3 Tage | 🔴 KRITISCH |
| **Phase 2: Compliance** | GDPR, Retention, Audit-Complete | 2-3 Tage | 🟡 WICHTIG |
| **Phase 3: UX** | Storage, Email, Progress, Preview, Batch | 2-3 Tage | 🟢 NICE-TO-HAVE |
| **TOTAL** | 10 Features | **6-10 Tage** | - |

---

## 🎯 EMPFOHLENER PLAN

### Option A: **SCHNELL** (Phase 1 only)
- **Dauer**: 2-3 Tage
- **Features**: Auth + Authorization + Rate-Limiting + Validation
- **Status danach**: ⚠️ **SICHER**, aber keine GDPR/UX
- **Production-Ready**: Nein (GDPR fehlt)

### Option B: **KOMPLETT** (Phase 1+2+3)
- **Dauer**: 6-10 Tage
- **Features**: ALLE 10 Features
- **Status danach**: ✅ **100% PRODUCTION-READY**
- **Empfehlung**: ✅ **JA** (für echten Launch)

### Option C: **HYBRID** (Phase 1+2)
- **Dauer**: 4-6 Tage
- **Features**: Security + Compliance
- **Status danach**: ✅ **PRODUCTION-READY** (UX kann später kommen)
- **Empfehlung**: ✅ **OPTIMAL** (Launch möglich, UX incrementell)

---

## 🚀 NÄCHSTE SCHRITTE

**Jetzt entscheiden**:
1. **Option A** (schnell, nur Security)
2. **Option B** (komplett, alle Features)
3. **Option C** (hybrid, Security + Compliance) ← **EMPFOHLEN**

**Dann starte ich mit**:
1. ✅ Fix syntax errors in case_management_tools.py
2. ✅ Implement Authentication in all tools
3. ✅ Implement Authorization in /api/v1/reports.py
4. ✅ Implement Tool-Rate-Limiting
5. ✅ GDPR Service (wenn Option B/C)
6. ✅ Storage/Email/Progress (wenn Option B)

---

**Warte auf deine Entscheidung!** 🎯
