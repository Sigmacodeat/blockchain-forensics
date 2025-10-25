# 📚 API DOCUMENTATION

**Version:** 1.0.0  
**Production Base URL:** `https://api.blockchain-forensics.com/api/v1`  
**Local Base URL (dev):** `http://localhost:8000/api/v1`

---

## 🔐 AUTHENTICATION

All API endpoints require authentication via JWT Bearer token:

```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

Get your token from `/api/v1/auth/login`

---

## 📊 ANALYTICS ENDPOINTS

### GET /analytics/real-time
Get real-time metrics (30s refresh)

**Response:**
```json
{
  "active_traces": 15,
  "active_cases": 8,
  "critical_alerts": 3,
  "active_users": 24,
  "timestamp": "2025-10-19T18:45:00Z"
}
```

### GET /analytics/threat-categories
Top threat categories

**Query Parameters:**
- `start_date` (optional): ISO date
- `end_date` (optional): ISO date
- `limit` (optional): Max results (default: 10)

**Response:**
```json
[
  {
    "category": "mixer",
    "count": 45,
    "avg_risk_score": 85.5,
    "percentage": 32.1
  }
]
```

### GET /analytics/risk-distribution
Risk distribution over time

**Query Parameters:**
- `start_date`, `end_date`, `interval` (day/week/month)

**Response:**
```json
[
  {
    "date": "2025-10-19",
    "critical": 5,
    "high": 12,
    "medium": 30,
    "low": 53,
    "total": 100
  }
]
```

### GET /analytics/export/csv
Export analytics as CSV

**Query Parameters:**
- `data_type`: threat_categories | risk_distribution | geographic
- `start_date`, `end_date`

**Response:** CSV File Download

### GET /analytics/export/excel
Export all analytics as Excel (multiple sheets)

**Response:** Excel File Download

---

## 🔍 TRACE ENDPOINTS

### POST /trace/start
Start a new transaction trace

**Request:**
```json
{
  "address": "0x1234...",
  "chain": "ethereum",
  "depth": 3,
  "direction": "both",
  "min_value_usd": 100
}
```

**Response:**
```json
{
  "trace_id": "trace_123",
  "status": "running",
  "estimated_duration_ms": 15000
}
```

### GET /trace/{trace_id}
Get trace results

**Response:**
```json
{
  "trace_id": "trace_123",
  "status": "completed",
  "nodes": [...],
  "edges": [...],
  "risk_summary": {...}
}
```

---

## 📁 CASE ENDPOINTS

### GET /cases
List all cases

**Query Parameters:**
- `status`: open | closed | archived
- `page`, `limit`

**Response:**
```json
{
  "cases": [...],
  "total": 45,
  "page": 1,
  "pages": 5
}
```

### POST /cases
Create new case

**Request:**
```json
{
  "title": "Investigation XYZ",
  "description": "...",
  "tags": ["fraud", "mixer"]
}
```

---

## 🔔 NOTIFICATION ENDPOINTS

### GET /notifications
Get user notifications

**Query Parameters:**
- `unread_only`: boolean
- `limit`: number

**Response:**
```json
[
  {
    "id": "notif_123",
    "title": "High-Risk Alert",
    "message": "...",
    "type": "alert",
    "priority": "high",
    "read": false,
    "created_at": "..."
  }
]
```

### POST /notifications/mark-all-read
Mark all as read

**Response:**
```json
{
  "count": 12
}
```

---

## 🎨 INTERACTIVE API DOCS

**Swagger UI (prod):** `https://api.blockchain-forensics.com/docs`  
**ReDoc (prod):** `https://api.blockchain-forensics.com/redoc`  
**OpenAPI Spec (prod):** `https://api.blockchain-forensics.com/openapi.json`  
**Swagger UI (local):** `http://localhost:8000/docs`  
**ReDoc (local):** `http://localhost:8000/redoc`  
**OpenAPI Spec (local):** `http://localhost:8000/openapi.json`

---

## 📊 RATE LIMITS

**Default:** 60 requests/minute per user  
**Premium:** 600 requests/minute  
**Enterprise:** Unlimited

**Headers:**
- `X-RateLimit-Limit`: Total limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp

---

## 🔒 SECURITY

### Headers Required:
```
Content-Type: application/json
Authorization: Bearer TOKEN
X-API-Version: v1
```

### CORS Allowed Origins:
- `https://blockchain-forensics.com`
- `https://*.blockchain-forensics.com`
- `http://localhost:3000` (dev)
- `http://localhost:5173` (dev)

---

## ❌ ERROR CODES

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid/missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

**Error Response:**
```json
{
  "error": "invalid_parameters",
  "message": "Missing required field: address",
  "details": {...}
}
```

---

## 📚 SDKs & LIBRARIES

**Python:**
```python
from blockchain_forensics import Client

client = Client(api_key="YOUR_KEY")
trace = client.trace.start(address="0x123...")
```

**JavaScript/TypeScript:**
```typescript
import { BlockchainForensics } from '@bf/sdk';

const client = new BlockchainForensics({ apiKey: 'YOUR_KEY' });
const trace = await client.trace.start({ address: '0x123...' });
```

**curl:**
```bash
curl -X POST https://api.blockchain-forensics.com/api/v1/trace/start \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"address":"0x123...","chain":"ethereum"}'
```

---

## WEBHOOKS

Configure webhooks in Dashboard → Settings → Webhooks

**Events:**
- `trace.completed`
- `alert.created`
- `case.updated`
- `payment.succeeded`

**Payload Example:**
```json
{
  "event": "trace.completed",
  "data": {...},
  "timestamp": "2025-10-19T18:45:00Z",
  "signature": "sha256_hmac..."
}
```

---

**FULL DOCS:** https://docs.blockchain-forensics.com
