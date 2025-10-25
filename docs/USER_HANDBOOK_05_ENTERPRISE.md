# 📘 Benutzerhandbuch Teil 5: Enterprise Features

> **Enterprise-Grade Compliance & Monitoring**

---

## ⚖️ 1. Multi-Sanctions Screening

### Was ist Multi-Sanctions?

**Automatisches Screening gegen 9 internationale Sanctions-Listen gleichzeitig.**

### 🌍 Supported Lists

| Jurisdiction | Liste | Updates | Entries |
|--------------|-------|---------|---------|
| 🇺🇸 **USA** | OFAC SDN | Daily | 12,000+ |
| 🇺🇳 **UN** | Security Council | Weekly | 3,500+ |
| 🇪🇺 **EU** | EU Sanctions | Daily | 8,000+ |
| 🇬🇧 **UK** | HM Treasury | Weekly | 4,500+ |
| 🇨🇦 **Canada** | OSI | Weekly | 2,800+ |
| 🇦🇺 **Australia** | DFAT | Monthly | 1,200+ |
| 🇨🇭 **Switzerland** | SECO | Weekly | 3,000+ |
| 🇯🇵 **Japan** | METI | Monthly | 1,500+ |
| 🇸🇬 **Singapore** | MAS | Monthly | 800+ |

**Total:** 37,300+ Sanctioned Entities

### 📖 Nutzung

#### API-Endpoint
```bash
POST /api/v1/sanctions/check
{
  "address": "0x1234...",
  "lists": ["OFAC", "UN", "EU"]  # Optional: All if empty
}

Response:
{
  "address": "0x1234...",
  "is_sanctioned": true,
  "matches": [
    {
      "list": "OFAC",
      "name": "LAZARUS GROUP",
      "added_date": "2023-11-15",
      "reference": "OFAC-12345",
      "reason": "Cyber Attacks, North Korea"
    }
  ],
  "checked_lists": 9,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### UI-Integration

**Auto-Check in Traces:**
```
Jeder Trace automatisch:
✅ Alle gefundenen Adressen
✅ Gegen alle 9 Listen
✅ Results in Summary
```

**Manual Check:**
```
Dashboard → Compliance → Sanctions Screening
[Enter Address] → [Check All Lists]
```

### 💡 Compliance-Features

**Legal Requirements:**
- ✅ FATF Recommendations
- ✅ EU AML Directives
- ✅ US Bank Secrecy Act
- ✅ UK Money Laundering Regulations

**Audit Trail:**
```json
{
  "check_id": "CHK-2024-001234",
  "address": "0x1234...",
  "timestamp": "2024-01-15T14:30:00Z",
  "checked_by": "compliance@company.com",
  "lists_checked": 9,
  "result": "MATCH",
  "action_taken": "ACCOUNT_FROZEN",
  "evidence_hash": "sha256:a3f7c2..."
}
```

---

## 🏦 2. VASP Directory & Travel Rule

### Was ist VASP Directory?

**Virtual Asset Service Provider Database - 5,000+ regulierte Exchanges, Wallets, Custodians.**

### 📊 Directory Coverage

**Sources:**
- **TRP Network** - 2,000+ VASPs
- **Notabene** - 1,500+ VASPs
- **OpenVASP** - 800+ VASPs
- **National Registries** - 700+ VASPs

**Regions:**
- 🌍 Global Coverage
- 🇺🇸 FinCEN Registered
- 🇪🇺 EU Licensed
- 🇯🇵 FSA Registered
- 🇸🇬 MAS Licensed

### 📖 VASP Lookup

**Identify VASP from Address:**
```bash
GET /api/v1/compliance/vasp-lookup?address=0x1234...

Response:
{
  "address": "0x1234...",
  "vasp": {
    "name": "Binance",
    "type": "Exchange",
    "jurisdiction": "Multiple",
    "licenses": ["FinCEN MSB", "EU MiFID"],
    "kyc_level": "Full KYC",
    "contact": "compliance@binance.com",
    "travel_rule_capable": true,
    "verification_status": "Verified"
  }
}
```

### 🔄 Travel Rule Compliance

**FATF Travel Rule = Transfer >$1000 erfordert Sender/Empfänger-Info.**

#### IVMS101 Format

**Standard-Message:**
```json
{
  "originator": {
    "name": "John Doe",
    "account": "0x1234...",
    "address": {
      "street": "123 Main St",
      "city": "New York",
      "country": "US"
    },
    "identification": {
      "type": "PASSPORT",
      "number": "P123456789"
    }
  },
  "beneficiary": {
    "name": "Jane Smith",
    "account": "0x5678...",
    "vasp": "Coinbase"
  },
  "transfer": {
    "amount": "1500 USD",
    "currency": "USDT",
    "date": "2024-01-15"
  }
}
```

#### API-Integration

**Send Travel Rule Data:**
```bash
POST /api/v1/compliance/travel-rule
{
  "transaction_hash": "0xabc...",
  "originator_vasp": "your-vasp-id",
  "beneficiary_vasp": "binance",
  "ivms101_data": { ... }
}
```

**Receive Travel Rule Data:**
```bash
# Webhook receives IVMS101
POST /api/v1/webhooks/travel-rule
{
  "event": "travel_rule.received",
  "data": { ... }
}
```

### 💡 Use Cases

**Compliance Workflow:**
```
1. Customer initiates withdrawal >$1000
2. System detects VASP destination (Binance)
3. Auto-generate IVMS101 message
4. Send via TRP/OpenVASP network
5. Wait for Beneficiary-VASP confirmation
6. Process transfer
7. Log for audit
```

---

## 📊 3. KYT Engine - Real-Time Monitoring

### Was ist KYT?

**Know Your Transaction = Real-Time Risk-Scoring für jede Transaction.**

### 🎯 Features

**Sub-100ms Latency:**
```
Transaction detected → Analyzed → Risk-Score → Alert
        <50ms           <30ms       <10ms      <10ms
                    Total: <100ms
```

**Checks (parallel):**
- ✅ Sanctions Lists (9)
- ✅ Mixer Detection
- ✅ High-Risk Addresses
- ✅ Velocity Rules
- ✅ Pattern Analysis

### 📖 Integration

#### WebSocket API

**Live-Stream:**
```javascript
const ws = new WebSocket('wss://api/v1/ws/kyt');

ws.on('message', (data) => {
  const tx = JSON.parse(data);
  
  if (tx.risk_score > 70) {
    // ALERT!
    console.log('High-Risk TX:', tx.hash);
    notifyCompliance(tx);
  }
});

// Send address to monitor
ws.send(JSON.stringify({
  action: 'monitor',
  addresses: ['0x1234...', '0x5678...']
}));
```

#### REST API

**Analyze Single TX:**
```bash
POST /api/v1/kyt/analyze
{
  "transaction_hash": "0xabc...",
  "chain": "ethereum"
}

Response:
{
  "hash": "0xabc...",
  "risk_level": "HIGH",
  "risk_score": 85,
  "reasons": [
    "Destination is known mixer",
    "Value >$100K",
    "Unusual timing pattern"
  ],
  "recommended_action": "HOLD_PENDING_REVIEW"
}
```

### �� Alert Rules

**Custom Rules:**
```json
{
  "name": "High-Value Mixer",
  "conditions": {
    "value_usd": { "gte": 10000 },
    "destination_type": "mixer"
  },
  "action": "FREEZE_AND_ALERT",
  "notification": ["email", "slack"]
}
```

**Pre-built Templates:**
- Sanctions Match (auto-block)
- High-Value to Mixer (alert)
- Rapid Succession Txs (velocity check)
- New Wallet Large Transfer (KYC verify)

---

## 📈 4. Analytics Dashboard (Admin Only)

### Was siehst du?

**System-Health & Investigation-Metrics für Admins.**

### 📊 Key Metrics

**Investigation Volume:**
```
┌────────────────────────────────────┐
│  📊 TRACES (Last 30 Days)          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Jan 15: ████████░░ 234            │
│  Jan 14: ██████░░░░ 187            │
│  Jan 13: ███████░░░ 201            │
│  ...                                │
│  Total: 6,543 (+12% vs last month) │
└────────────────────────────────────┘
```

**Risk Distribution:**
```
┌────────────────────────────────────┐
│  🚨 RISK DISTRIBUTION              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Critical (81-100): 5%  ████       │
│  High (61-80):      12% ████████   │
│  Medium (31-60):    28% ████████████│
│  Low (0-30):        55% ████████████│
└────────────────────────────────────┘
```

**Top Findings:**
```
┌────────────────────────────────────┐
│  🔥 TOP THREAT CATEGORIES          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  1. Mixer Activity        847      │
│  2. Sanctions Contact     234      │
│  3. High-Risk Exchanges   156      │
│  4. Scam/Phishing         89       │
│  5. Ransomware            23       │
└────────────────────────────────────┘
```

### 🛠️ Admin-Features

**User Management:**
- Active Users
- Plan Distribution
- Usage Quotas
- Billing Status

**System Performance:**
- API Latency (p50, p95, p99)
- Database Query Times
- Cache Hit-Rates
- Error Rates

**Audit Logs:**
```
timestamp,user,action,resource,result
2024-01-15T14:30:00,john@fbi.gov,trace_started,0x1234...,success
2024-01-15T14:31:00,sarah@europol.eu,case_created,CASE-007,success
2024-01-15T14:32:00,max@police.de,evidence_exported,report.pdf,success
```

---

## 🔐 5. Organization Management

### Multi-Tenancy für Agencies

**Features:**
- 👥 Unlimited Users
- 🏢 Department Hierarchy
- 🔐 Role-Based Access
- 📊 Org-Wide Analytics
- 💾 Shared Cases

### 📖 Organization Setup

**Structure:**
```
Organization: Federal Cyber Crime Unit
├── Department: Investigations
│   ├── Team: Ransomware Squad
│   │   ├── Lead Investigator (Admin)
│   │   ├── Analyst 1 (Editor)
│   │   └── Analyst 2 (Editor)
│   └── Team: Exchange Hacks
│       └── ...
├── Department: Compliance
│   └── Team: AML Screening
│       └── ...
└── Department: Legal
    └── Team: Evidence Management
        └── ...
```

**Permissions Matrix:**

| Role | Traces | Cases | Evidence | Reports | Admin |
|------|--------|-------|----------|---------|-------|
| **Org Admin** | ✅ All | ✅ All | ✅ All | ✅ All | ✅ All |
| **Dept Manager** | ✅ Dept | ✅ Dept | ✅ View | ✅ Dept | ⚠️ Limited |
| **Team Lead** | ✅ Team | ✅ Team | ✅ Upload | ✅ Team | ❌ No |
| **Investigator** | ✅ Own | ✅ Assigned | ✅ Upload | ✅ Own | ❌ No |
| **Analyst** | ✅ View | ✅ View | ✅ View | ✅ View | ❌ No |

### 💡 Use Cases

**Inter-Agency Collaboration:**
```
FBI Case #12345
├── Shared with: Europol (View-Only)
├── Shared with: Local PD (Editor)
└── Evidence: Court-Approved Only
```

**Case-Handoff:**
```
1. Local PD: Initial Investigation
2. Escalate → FBI: Federal Case
3. Transfer ownership + all evidence
4. Continue monitoring by Local PD
```

---

## 🔌 6. API Integration

### REST API

**Base URL:** `https://api.platform.com/api/v1`

**Authentication:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.platform.com/api/v1/trace
```

**Key Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/trace` | POST | Start trace |
| `/cases` | GET/POST | List/Create cases |
| `/sanctions/check` | POST | Sanctions screening |
| `/risk/score` | GET | Risk scoring |
| `/evidence/export` | GET | Export evidence |

**Rate Limits:**
- Community: 100 req/hour
- Pro: 1,000 req/hour
- Enterprise: Unlimited

### Webhooks

**Subscribe to Events:**
```json
{
  "webhook_url": "https://your-server.com/webhook",
  "events": [
    "trace.completed",
    "case.updated",
    "alert.triggered",
    "sanctions.match"
  ]
}
```

**Event Payload:**
```json
{
  "event": "alert.triggered",
  "timestamp": "2024-01-15T14:30:00Z",
  "data": {
    "alert_id": "ALERT-001234",
    "type": "high_risk_transaction",
    "address": "0x1234...",
    "risk_score": 85,
    "reason": "Mixer detected"
  }
}
```

### Python SDK

```python
from blockchain_forensics import Client

client = Client(api_key="YOUR_KEY")

# Start trace
trace = client.trace("0x1234...", depth=5)

# Check sanctions
sanctions = client.sanctions.check("0x1234...")

if sanctions.is_sanctioned:
    print(f"MATCH: {sanctions.matches[0].list}")

# Create case
case = client.cases.create(
    title="Investigation",
    addresses=["0x1234...", "0x5678..."]
)

# Export report
pdf = case.export_pdf()
pdf.save("report.pdf")
```

### Integration Examples

**Slack Bot:**
```python
@bot.command("/check-address")
async def check_address(ctx, address):
    result = client.risk.score(address)
    
    if result.score > 70:
        await ctx.send(f"⚠️ HIGH RISK: {result.score}/100")
    else:
        await ctx.send(f"✅ Low Risk: {result.score}/100")
```

**Automated Screening:**
```python
# Cron Job: Daily screening
def daily_screen():
    wallets = get_company_wallets()
    
    for wallet in wallets:
        result = client.kyt.analyze(wallet)
        
        if result.risk_level == "HIGH":
            alert_compliance(wallet, result)
            freeze_account(wallet)
```

---

**➡️ Zurück zum [Index](USER_HANDBOOK_INDEX.md)**
