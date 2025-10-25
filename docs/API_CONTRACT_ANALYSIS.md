# Smart Contract Analysis API - Quick Reference

## Endpunkte

### 1. Deep Contract Analysis

**POST** `/api/v1/contracts/analyze`

**Requires:** Pro Plan

**Request:**
```json
{
  "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
  "chain": "ethereum",
  "include_bytecode": false
}
```

**Response:**
```json
{
  "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
  "chain": "ethereum",
  "score": 0.35,
  "risk_level": "low",
  "findings": [
    {
      "id": "vuln_reentrancy",
      "kind": "reentrancy",
      "severity": "critical",
      "evidence": "External call at offset 120 followed by state change...\nRemediation: Use Checks-Effects-Interactions pattern..."
    }
  ],
  "summary": "Contract implements: ERC20\n✅ No major vulnerabilities or exploits detected",
  "interface": {
    "standards": ["ERC20", "Ownable"],
    "is_proxy": false,
    "functions_count": 12,
    "top_functions": [
      {
        "selector": "0xa9059cbb",
        "signature": "transfer(address,uint256)",
        "name": "transfer"
      }
    ]
  },
  "statistics": {
    "total_opcodes": 1245,
    "unique_opcodes": 45,
    "complexity_score": 0.23,
    "external_calls": 5,
    "storage_operations": 18,
    "has_selfdestruct": false,
    "delegatecall_count": 0
  },
  "vulnerabilities": {
    "total": 1,
    "critical": 1,
    "high": 0,
    "medium": 0,
    "low": 0
  }
}
```

---

### 2. Quick Analysis (GET)

**GET** `/api/v1/contracts/analyze/{chain}/{address}`

**Requires:** Pro Plan

**Example:**
```bash
curl "https://api.yourplatform.com/api/v1/contracts/analyze/ethereum/0xdac17f958d2ee523a2206206994597c13d831ec7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. Function Signature Lookup

**POST** `/api/v1/contracts/function/lookup`

**Requires:** Community Plan

**Request:**
```json
{
  "selector": "0xa9059cbb"
}
```

**Response:**
```json
{
  "selector": "0xa9059cbb",
  "signature": "transfer(address,uint256)",
  "name": "transfer",
  "params": ["address", "uint256"],
  "source": "local",
  "confidence": 0.95
}
```

---

### 4. Function Lookup (GET)

**GET** `/api/v1/contracts/function/{selector}`

**Requires:** Community Plan

**Example:**
```bash
curl "https://api.yourplatform.com/api/v1/contracts/function/0xa9059cbb" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 5. Detect ERC Standards

**GET** `/api/v1/contracts/standards/{chain}/{address}`

**Requires:** Pro Plan

**Example:**
```bash
curl "https://api.yourplatform.com/api/v1/contracts/standards/ethereum/0xdac17f958d2ee523a2206206994597c13d831ec7" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
  "chain": "ethereum",
  "standards": ["ERC20"],
  "is_proxy": false,
  "functions_count": 12
}
```

---

### 6. Health Check

**GET** `/api/v1/contracts/health`

**Public** - No authentication required

**Response:**
```json
{
  "status": "healthy",
  "service": "contract_analysis",
  "features": [
    "bytecode_analysis",
    "vulnerability_detection",
    "exploit_recognition",
    "function_signature_matching",
    "interface_detection"
  ]
}
```

---

## Unterstützte Chains

- ✅ `ethereum`
- ✅ `polygon`
- ✅ `bsc`
- ✅ `arbitrum`
- ✅ `optimism`
- ✅ `base`

---

## Risk Levels

| Score | Level | Description |
|-------|-------|-------------|
| 0.0-0.2 | **minimal** | Safe contract, no significant issues |
| 0.2-0.4 | **low** | Minor concerns, generally safe |
| 0.4-0.6 | **medium** | Some risks, use with caution |
| 0.6-0.8 | **high** | Significant vulnerabilities found |
| 0.8-1.0 | **critical** | Dangerous contract, avoid interaction |

---

## Severity Levels

| Severity | Color | Action |
|----------|-------|--------|
| **critical** | 🔴 Red | Do not interact! |
| **high** | 🟠 Orange | High risk, investigate thoroughly |
| **medium** | 🟡 Yellow | Moderate risk, proceed with caution |
| **low** | 🟢 Green | Minor issue, informational |
| **info** | 🔵 Blue | Informational only |

---

## Erkannte Vulnerabilities

1. **Reentrancy** (CRITICAL) - CWE-841
2. **Integer Overflow/Underflow** (MEDIUM) - CWE-190
3. **Unchecked External Calls** (MEDIUM) - CWE-252
4. **Access Control Issues** (CRITICAL) - CWE-284
5. **DELEGATECALL Injection** (CRITICAL) - CWE-829
6. **Timestamp Dependence** (MEDIUM) - CWE-330
7. **tx.origin Authentication** (HIGH) - CWE-477
8. **Unprotected SELFDESTRUCT** (CRITICAL)
9. **Frontrunning Risks** (LOW)
10. **Gas Limit DoS** (MEDIUM)

---

## Exploit Patterns

### Flash Loan Attacks
- Balance-based Price Oracle
- Multiple External Calls
- Real Cases: bZx, Harvest Finance, Cream Finance

### Honeypot Contracts
- tx.origin Checks
- Owner-Only Transfer
- Hidden Logic

### Rugpull Indicators
- SELFDESTRUCT Capability
- Unrestricted DELEGATECALL
- Multiple Owner Functions
- Pausable without Timelock

### Oracle Manipulation
- Spot Balance Usage
- No Time-Weighted Average
- Single-Source Price Data

---

## ERC Standards Detection

Automatisch erkannt:
- ✅ **ERC20** - Fungible Tokens
- ✅ **ERC721** - NFTs
- ✅ **ERC1155** - Multi-Token
- ✅ **Ownable** - Ownership Management
- ✅ **Pausable** - Emergency Stop
- ✅ **Proxy** - Upgradeable Contracts

---

## Beispiel-Integration

### JavaScript/TypeScript
```typescript
const analyzeContract = async (address: string, chain: string = 'ethereum') => {
  const response = await fetch('/api/v1/contracts/analyze', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ address, chain }),
  });
  
  const result = await response.json();
  
  // Check risk level
  if (result.risk_level === 'critical') {
    alert('⚠️ DANGER! This contract is highly risky!');
  }
  
  // Display findings
  result.findings.forEach(finding => {
    console.log(`${finding.severity}: ${finding.evidence}`);
  });
  
  return result;
};
```

### Python
```python
import requests

def analyze_contract(address: str, chain: str = "ethereum"):
    response = requests.post(
        "https://api.yourplatform.com/api/v1/contracts/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"address": address, "chain": chain}
    )
    
    result = response.json()
    
    # Check for critical vulnerabilities
    if result["vulnerabilities"]["critical"] > 0:
        print("⚠️ CRITICAL vulnerabilities found!")
    
    # Print summary
    print(result["summary"])
    
    return result
```

---

## Error Handling

### 400 Bad Request
```json
{
  "detail": "No bytecode found - not a contract or contract destroyed"
}
```

### 404 Not Found
```json
{
  "detail": "No signature found for selector 0x12345678"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Analysis failed: RPC error: ..."
}
```

---

## Rate Limits

| Plan | Requests/Hour | Concurrent |
|------|---------------|------------|
| Community | 100 | 2 |
| Pro | 1,000 | 10 |
| Business | 10,000 | 50 |
| Enterprise | Unlimited | Unlimited |

---

## Best Practices

1. **Cache Results** - Analysis ist rechenintensiv
2. **Use Async** - Für bessere Performance
3. **Check Risk Level** - Vor User-Interaktion warnen
4. **Monitor Critical** - Alerts für critical findings
5. **Batch Processing** - Für große Mengen Contracts

---

## Support

- 📧 Email: support@yourplatform.com
- 📚 Docs: https://docs.yourplatform.com
- 💬 Discord: https://discord.gg/yourplatform
