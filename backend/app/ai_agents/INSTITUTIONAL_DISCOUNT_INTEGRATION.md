# 🏛️ INSTITUTIONAL DISCOUNT - AI-AGENT INTEGRATION

## Tools zu registrieren in `backend/app/ai_agents/tools.py`:

```python
# In tools.py importieren:
from app.ai_agents.tools.institutional_verification_tools import (
    INSTITUTIONAL_VERIFICATION_TOOLS
)

# In FORENSIC_TOOLS Liste hinzufügen:
FORENSIC_TOOLS = [
    # ... existing tools ...
    
    # Institutional Verification Tools (3 neue)
    *INSTITUTIONAL_VERIFICATION_TOOLS,
]
```

---

## System-Prompt Erweiterung in `backend/app/ai_agents/agent.py`:

```python
FORENSICS_SYSTEM_PROMPT = """
# ... existing prompt ...

## INSTITUTIONAL DISCOUNT SYSTEM

You have access to tools for institutional discount management:

**Available to:**
- 🚔 Police & Law Enforcement
- 🔍 Private Investigators & Agencies
- ⚖️ Lawyers & Prosecutors
- 🏛️ Government Agencies
- 🏦 Crypto Exchanges & Financial Institutions

**Discount Structure:**
- Annual Billing: 20% discount (standard)
- Institutional: +10% discount (after verification)
- **TOTAL: 30% savings** for verified institutions

**Verification Methods:**
1. **Auto-Verification (Instant):**
   - Trusted email domains (@polizei.de, @fbi.gov, .gov, etc.)
   - Use `check_discount_eligibility` to check
   - Instant activation if domain is trusted

2. **Manual Verification (24-48h):**
   - Upload documents (ID, License, Business Registration)
   - Admin reviews within 24-48 hours
   - User can upload via chat, web, or email

**Tools:**
1. `check_institutional_status`: Check user's current status
2. `request_institutional_verification`: Start verification process
3. `check_discount_eligibility`: Check if email domain qualifies for auto-verification

**Conversation Flow:**

User: "Ich bin Polizist, gibt es Rabatt?"

AI Response:
"Ja! Als Polizist erhalten Sie 10% institutionellen Rabatt zusätzlich zu unserem 
Jahresrabatt (20%). Das sind insgesamt 30% Ersparnis!

Beispiel Pro Plan:
- Normal: $1,188/Jahr
- Mit Rabatten: $855/Jahr
- Sie sparen: $333/Jahr

Um den Rabatt zu aktivieren:
[check_discount_eligibility with user's email]

Wenn Auto-Verification möglich:
  ✅ Ihr Email-Domain ist verifiziert! Soll ich den Rabatt sofort aktivieren?
  
Wenn Dokumente nötig:
  📄 Bitte laden Sie Ihren Dienstausweis hoch:
  - Hier im Chat
  - Auf der Verification-Page: /verify
  - Per Email: verify@sigmacode.io

Möchten Sie jetzt starten?"

**Important:**
- ALWAYS mention 30% total savings (20% + 10%)
- ALWAYS check eligibility first
- ALWAYS explain verification process
- ALWAYS provide upload options
- BE PROACTIVE: If user mentions police/detective/lawyer, offer discount immediately
"""
```

---

## Beispiel-Konversationen:

### Szenario 1: Auto-Verification (Polizei mit @polizei.de Email)

```
User: "Ich bin von der Polizei Berlin, bekomme ich Rabatt?"

AI: [calls check_institutional_status]
    → User hat noch keinen Rabatt

AI: "Ja! Als Polizist erhalten Sie 10% institutionellen Rabatt. 
     Zusammen mit 20% Jahresrabatt sind das 30% Ersparnis!
     
     Pro Plan Beispiel:
     • Standard: $1,188/Jahr
     • Ihr Preis: $855/Jahr  
     • Ersparnis: $333
     
     Darf ich Ihre Email prüfen?"

User: "Ja, meine Email ist m.mueller@polizei.de"

AI: [calls check_discount_eligibility with email]
    → eligible: true, auto_verification: true

AI: "✅ Perfekt! Ihre Email-Domain (@polizei.de) ist als vertrauenswürdig 
     registriert. Ich kann den Rabatt sofort aktivieren!
     
     Soll ich fortfahren?"

User: "Ja bitte"

AI: [calls request_institutional_verification]
    → status: auto_approved

AI: "🎉 Fertig! Ihr institutioneller Rabatt ist aktiviert!
     
     ✅ 10% Institutional Discount: AKTIV
     ✅ 20% Annual Discount: Verfügbar
     ✅ Gesamt: 30% Ersparnis
     
     Sie zahlen jetzt nur $855/Jahr statt $1,188.
     
     Möchten Sie direkt einen Plan auswählen?"
```

### Szenario 2: Manuelle Verification (Privatdetektiv)

```
User: "Ich bin Privatdetektiv, gibt es für mich auch Rabatt?"

AI: [calls check_institutional_status]
    → User hat noch keinen Rabatt

AI: "Ja! Als Privatdetektiv erhalten Sie 10% institutionellen Rabatt!
     Zusammen mit 20% Jahresrabatt: 30% Gesamt-Ersparnis.
     
     Pro Plan: $855/Jahr (statt $1,188) → Sie sparen $333
     
     Um den Rabatt zu aktivieren, benötige ich einen Nachweis:
     ✅ Gewerbeanmeldung
     ✅ IHK-Registrierung
     ✅ Detektiv-Lizenz
     
     Wo möchten Sie hochladen?"

User: "Hier im Chat"

AI: "Perfekt! Laden Sie Ihre Dokumente hier hoch.
     
     Akzeptierte Formate: PDF, JPG, PNG (max 10MB)
     
     Nach Upload:
     • Admin-Review: 24-48 Stunden
     • Email-Benachrichtigung bei Approval
     • Rabatt automatisch aktiviert
     
     Soll ich die Verification jetzt starten?"

User: "Ja"

AI: [calls request_institutional_verification with organization_type='detective']
    → status: verification_started

AI: "✅ Verification gestartet!
     
     Nächste Schritte:
     1. Laden Sie Dokumente hoch (hier oder /verify)
     2. Admin prüft binnen 24-48h
     3. Bei Approval: Rabatt sofort aktiv
     
     Upload-Link: /verify/12345
     
     Sie können die Dokumente auch per Email senden: verify@sigmacode.io"
```

### Szenario 3: Status-Check

```
User: "Was ist der Status meiner Verification?"

AI: [calls check_institutional_status]
    → verification_status: pending

AI: "⏳ Ihre Verification läuft:
     
     Status: In Prüfung
     Organisation: Privatdetektiv
     Eingereicht: vor 12 Stunden
     
     Erwartete Bearbeitung: 24-48 Stunden
     
     Sobald approved:
     ✅ 10% Rabatt automatisch aktiv
     ✅ Email-Benachrichtigung
     ✅ Sofort nutzbar
     
     Möchten Sie zusätzliche Dokumente hochladen?"
```

---

## Marketing-Integration

### Use-Case-Pages Chatbot-Prompts:

Wenn User auf `/use-cases/police` ist:

```python
if user_on_page == '/use-cases/police':
    proactive_message = """
    💡 Als Polizist erhalten Sie 10% Sonderrabatt!
    
    Zusammen mit Jahresrabatt: 30% Ersparnis
    Ihr Preis: $855/Jahr (statt $1,188)
    
    Möchten Sie den Rabatt aktivieren?
    """
```

### Pricing-Page Integration:

Wenn User auf `/pricing` ist und `organization_type` gesetzt:

```python
if user.organization_type and not user.institutional_discount_verified:
    chatbot_prompt = f"""
    🏛️ Sie sind als {user.organization_type} registriert!
    
    Sie können 10% institutionellen Rabatt beantragen.
    
    Soll ich die Verification für Sie starten?
    """
```

---

## Analytics Events

Track folgende Events:

```typescript
// Institutional Discount Events
track('institutional_discount_requested', {
  organization_type: string,
  auto_verified: boolean
})

track('institutional_discount_approved', {
  organization_type: string,
  verification_method: 'auto' | 'manual',
  time_to_approval_hours: number
})

track('institutional_discount_used', {
  organization_type: string,
  plan: string,
  savings_amount: number
})
```

---

## Admin Notifications

Bei neuer Verification-Request:

```
Subject: 🏛️ New Institutional Verification - {organization_type}

User: {username} ({email})
Organization: {organization_name}
Type: {organization_type}
Documents: {count}

Review now: /admin/verifications/{id}
```

---

**Status:** Integration-Guide Complete  
**Ready to:** Implement in tools.py & agent.py
