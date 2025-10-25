# 🔒 SECURITY GUIDE

**Security First - Best Practices**

---

## 🛡️ SECURITY HEADERS

### Required Headers:
```nginx
# Content Security Policy
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://api.blockchain-forensics.com

# Strict Transport Security (HSTS)
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

# X-Frame-Options
X-Frame-Options: DENY

# X-Content-Type-Options
X-Content-Type-Options: nosniff

# Referrer Policy
Referrer-Policy: strict-origin-when-cross-origin

# Permissions Policy
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

---

## 🔐 AUTHENTICATION & AUTHORIZATION

### JWT Security:
- **Algorithm:** RS256 (RSA)
- **Expiration:** 15 minutes (Access Token)
- **Refresh Token:** 7 days
- **Storage:** HttpOnly Cookies

### Password Requirements:
- Minimum 12 characters
- Uppercase + Lowercase + Numbers + Special
- bcrypt hashing (cost: 12)
- No common passwords (leaked DB check)

---

## 🚫 RATE LIMITING

### Limits:
- **Login Attempts:** 5 per 15 minutes
- **API Calls:** 60 per minute (user)
- **Password Reset:** 3 per hour
- **Registration:** 5 per hour (IP)

### Implementation:
```python
from fastapi_limiter import RateLimiter

@router.post("/login")
@RateLimiter(times=5, seconds=900)
async def login(...):
    ...
```

---

## 🔒 INPUT VALIDATION

### All Inputs Validated:
- **Addresses:** Regex + Checksum validation
- **Amounts:** Positive numbers only
- **Strings:** Max length + XSS sanitization
- **Files:** Type + Size validation

### Example:
```python
from pydantic import BaseModel, validator

class TraceRequest(BaseModel):
    address: str
    
    @validator('address')
    def validate_address(cls, v):
        if not is_valid_ethereum_address(v):
            raise ValueError('Invalid address')
        return v.lower()
```

---

## 🛡️ XSS PROTECTION

### Frontend:
- React escapes by default ✅
- No `dangerouslySetInnerHTML` ✅
- CSP Headers ✅
- Input Sanitization ✅

### Backend:
- HTML Escaping in responses
- Parameterized SQL queries
- No eval() or exec()

---

## 🔐 CSRF PROTECTION

### Implementation:
- CSRF tokens in forms
- SameSite cookies
- Origin verification
- Double-submit pattern

```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/api/v1/cases")
async def create_case(csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    ...
```

---

## 🗄️ DATABASE SECURITY

### Best Practices:
- Parameterized queries (SQLAlchemy) ✅
- Least privilege principle ✅
- Encrypted connections (SSL/TLS) ✅
- Regular backups ✅
- No sensitive data in logs ✅

---

## 🔑 SECRETS MANAGEMENT

### Environment Variables:
```bash
# Never commit .env files!
DATABASE_URL=postgresql://...
JWT_SECRET=random_256_bit_key
API_KEYS=...
```

### Production:
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets

---

## 📊 SECURITY MONITORING

### Tools:
- **SAST:** Bandit, Semgrep
- **DAST:** OWASP ZAP
- **Dependency Scanning:** Snyk, Dependabot
- **Log Monitoring:** Sentry, Datadog

### Alerts:
- Failed login attempts
- Rate limit violations
- Suspicious patterns
- Error spikes

---

## ✅ SECURITY CHECKLIST

### Application:
- [x] HTTPS Everywhere
- [x] Security Headers configured
- [x] Input validation
- [x] XSS Prevention
- [x] CSRF Protection
- [x] SQL Injection Prevention
- [x] Rate Limiting
- [x] Authentication secure
- [x] Secrets not in code

### Infrastructure:
- [x] Firewall configured
- [x] DDoS Protection (Cloudflare)
- [x] Database encrypted
- [x] Backups automated
- [x] Monitoring active

### Compliance:
- [x] GDPR Compliant
- [x] Privacy Policy
- [x] Terms of Service
- [x] Cookie Consent
- [x] Data Processing Agreement

---

## 🚨 INCIDENT RESPONSE

### Plan:
1. **Detect:** Monitoring alerts
2. **Contain:** Isolate affected systems
3. **Eradicate:** Remove threat
4. **Recover:** Restore services
5. **Review:** Post-mortem analysis

### Contacts:
- Security Team: security@blockchain-forensics.com
- On-Call: +1-XXX-XXX-XXXX

---

**STATUS:** ✅ SECURED
**LAST AUDIT:** 2025-10-19
**NEXT AUDIT:** 2025-11-19
