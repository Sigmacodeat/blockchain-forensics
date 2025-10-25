# 🏛️ INSTITUTIONELLER RABATT-SYSTEM - COMPLETE SPEC

## 🎯 ÜBERBLICK

**Ziel:** 10% zusätzlicher Rabatt für verifizierte Institutionen (Polizei, Detektive, Anwälte, Regierungen)

**Gesamt-Rabatt-Struktur:**
```
Jahresabo:           20% (besteht bereits)
Institutionell:     +10% (NEU)
──────────────────────────────────
TOTAL:               30% für verifizierte Institutionen mit Jahresabo
```

**Zielgruppen:**
1. 🚔 Polizei & Ermittlungsbehörden
2. 🔍 Privatdetektive & Investigation Agencies
3. ⚖️ Anwälte & Staatsanwälte
4. 🏛️ Regierungen & Behörden

---

## 📋 FEATURE REQUIREMENTS

### 1. REGISTRATION FLOW

#### Organization-Selection (Optional aber empfohlen)

**Neue Felder im Registration-Form:**
```tsx
{
  // Bestehende Felder
  email: string
  password: string
  username: string
  
  // NEUE Felder
  organization_type?: 'police' | 'detective' | 'lawyer' | 'government' | 'exchange' | 'other'
  organization_name?: string
  wants_institutional_discount?: boolean
}
```

**UI-Design:**
```
┌─────────────────────────────────────────┐
│  Registrierung                          │
├─────────────────────────────────────────┤
│  Email: ___________________________     │
│  Password: ________________________     │
│  Username: ________________________     │
│                                         │
│  ┌───────────────────────────────┐     │
│  │ 💡 Sind Sie von einer         │     │
│  │    Institution?               │     │
│  │                               │     │
│  │ ✅ Erhalten Sie 10% Rabatt!  │     │
│  └───────────────────────────────┘     │
│                                         │
│  Organization Type: [Dropdown ▼]       │
│  ┌─────────────────────────────┐       │
│  │ 🚔 Polizei/Ermittlungsbehörde│       │
│  │ 🔍 Privatdetektiv/Agentur    │       │
│  │ ⚖️ Anwalt/Staatsanwalt       │       │
│  │ 🏛️ Regierung/Behörde         │       │
│  │ 🏦 Exchange/Bank             │       │
│  │ 👤 Andere                    │       │
│  └─────────────────────────────┘       │
│                                         │
│  Organization Name: _______________     │
│  (optional, z.B. "LKA Berlin")          │
│                                         │
│  [ ] Ich möchte 10% institutionellen   │
│      Rabatt beantragen (Nachweis       │
│      erforderlich)                      │
│                                         │
│  [Registrieren]                         │
└─────────────────────────────────────────┘
```

---

### 2. DATABASE SCHEMA

**User-Model Erweiterungen:**

```sql
-- Neue Spalten in users table
ALTER TABLE users ADD COLUMN organization_type VARCHAR(50);
ALTER TABLE users ADD COLUMN organization_name VARCHAR(255);
ALTER TABLE users ADD COLUMN institutional_discount_requested BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN institutional_discount_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN verification_status VARCHAR(50) DEFAULT 'none'; 
-- Werte: 'none', 'pending', 'approved', 'rejected'
ALTER TABLE users ADD COLUMN verification_documents TEXT; 
-- JSON array von Upload-URLs
ALTER TABLE users ADD COLUMN verification_notes TEXT;
ALTER TABLE users ADD COLUMN verified_at TIMESTAMP;
ALTER TABLE users ADD COLUMN verified_by INTEGER REFERENCES users(id);
```

**Verification-Documents Table (Optional):**

```sql
CREATE TABLE institutional_verifications (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  organization_type VARCHAR(50) NOT NULL,
  organization_name VARCHAR(255),
  
  -- Dokumente
  document_type VARCHAR(50), -- 'id_card', 'business_license', 'email_verification'
  document_url TEXT,
  document_filename VARCHAR(255),
  
  -- Status
  status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
  reviewed_by INTEGER REFERENCES users(id),
  reviewed_at TIMESTAMP,
  
  -- Notizen
  admin_notes TEXT,
  rejection_reason TEXT,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### 3. NACHWEIS-METHODEN

#### Option A: Dienstausweis-Upload

**Akzeptierte Dokumente:**
- Polizei: Dienstausweis, Polizeiausweis
- Detektive: Gewerbelizenz, IHK-Nachweis
- Anwälte: Anwaltszulassung, BAR Association
- Regierungen: Behörden-Email, Dienstausweis

**Upload-Flow:**
```
1. User wählt bei Registration "Institutional Discount"
2. Nach Registration → Redirect zu Verification-Page
3. Upload Dienstausweis/Lizenz
4. AI-Chatbot kann auch Upload entgegennehmen
5. Admin reviewt → Approve/Reject
6. User wird benachrichtigt (Email + In-App)
7. Bei Approval: Discount automatisch aktiv
```

#### Option B: Email-Domain-Verification (Automatisch)

**Vertrauenswürdige Domains:**
```typescript
const TRUSTED_DOMAINS = {
  police: [
    'polizei.de',
    'polizei.bund.de',
    'lka.*.de',
    'bka.de',
    'fbi.gov',
    'police.uk',
    // etc.
  ],
  government: [
    'bund.de',
    'gov',
    'gov.uk',
    'gouv.fr',
    // etc.
  ],
  // etc.
}
```

**Auto-Verification:**
```typescript
async function checkEmailDomain(email: string): Promise<boolean> {
  const domain = email.split('@')[1]
  
  // Check gegen Trusted-Domains
  if (TRUSTED_DOMAINS.police.some(d => domain.endsWith(d))) {
    return true
  }
  
  // Oder per DNS-Lookup für Regierungs-Domains
  // ...
  
  return false
}
```

#### Option C: Manuelle Verification (Admin)

**Admin-Panel:**
```
Pending Verifications (12)
┌──────────────────────────────────────────────────┐
│ User: Max Mustermann                             │
│ Email: m.mustermann@lka-berlin.de               │
│ Org Type: Polizei                                │
│ Org Name: LKA Berlin                             │
│ Requested: 19.10.2025 18:30                     │
│                                                  │
│ Documents:                                       │
│ - dienstausweis.pdf [View]                      │
│ - lka_bestaetigung.pdf [View]                   │
│                                                  │
│ [✅ Approve] [❌ Reject] [💬 Request More Info] │
└──────────────────────────────────────────────────┘
```

---

### 4. BILLING-INTEGRATION

**Rabatt-Kalkulation:**

```typescript
interface PricingCalculation {
  base_price: number
  annual_discount: number // 20%
  institutional_discount: number // 10% (nur wenn verified)
  final_price: number
}

function calculatePrice(
  plan: Plan,
  billing_cycle: 'monthly' | 'annual',
  user: User
): PricingCalculation {
  let base_price = plan.monthly_price_usd
  
  // Jahresrabatt
  let annual_discount = 0
  if (billing_cycle === 'annual') {
    annual_discount = base_price * 12 * 0.20
    base_price = base_price * 12 * 0.80
  }
  
  // Institutioneller Rabatt (nur wenn verifiziert)
  let institutional_discount = 0
  if (user.institutional_discount_verified) {
    institutional_discount = base_price * 0.10
    base_price = base_price * 0.90
  }
  
  return {
    base_price: plan.monthly_price_usd * (billing_cycle === 'annual' ? 12 : 1),
    annual_discount,
    institutional_discount,
    final_price: base_price
  }
}

// Beispiel:
// Pro Plan: $99/Monat
// Jahresabo: $99 * 12 * 0.80 = $950 (statt $1,188)
// + Institutional: $950 * 0.90 = $855
// TOTAL SAVINGS: $333 (28% gesamt!)
```

**Pricing-Page Anzeige:**

```tsx
<PricingCard plan="pro">
  <Price>
    <Original>$1,188/Jahr</Original>
    <Discount annual>-$238 (20%)</Discount>
    
    {user.institutional_discount_verified && (
      <Discount institutional>-$95 (10%)</Discount>
    )}
    
    <Final>$855/Jahr</Final>
    
    {!user.institutional_discount_verified && user.organization_type && (
      <Badge color="blue">
        ✅ Verify your institution for an additional 10% off!
        <Link to="/verify">Verify Now</Link>
      </Badge>
    )}
  </Price>
</PricingCard>
```

---

### 5. CHATBOT-INTEGRATION

**Neue AI-Agent Tools:**

#### Tool 1: check_institutional_status

```typescript
{
  name: "check_institutional_status",
  description: "Check if user has institutional discount and verification status",
  parameters: {
    user_id: number
  },
  async execute({ user_id }) {
    const user = await db.users.findById(user_id)
    
    return {
      has_institutional_discount: user.institutional_discount_verified,
      organization_type: user.organization_type,
      verification_status: user.verification_status,
      discount_amount: user.institutional_discount_verified ? '10%' : '0%',
      can_request: !user.institutional_discount_requested
    }
  }
}
```

#### Tool 2: request_institutional_verification

```typescript
{
  name: "request_institutional_verification",
  description: "Start institutional verification process",
  parameters: {
    user_id: number,
    organization_type: string,
    organization_name: string
  },
  async execute({ user_id, organization_type, organization_name }) {
    await db.users.update(user_id, {
      organization_type,
      organization_name,
      institutional_discount_requested: true,
      verification_status: 'pending'
    })
    
    // Send Email mit Upload-Link
    await sendVerificationEmail(user_id)
    
    return {
      status: 'verification_started',
      message: 'Verification request submitted. Please upload your documents.',
      upload_link: `/verify/${user_id}`
    }
  }
}
```

#### Tool 3: upload_verification_document (via Chat)

```typescript
{
  name: "upload_verification_document",
  description: "Handle document upload for institutional verification",
  parameters: {
    user_id: number,
    document_type: string,
    file_url: string // From chat file-upload
  },
  async execute({ user_id, document_type, file_url }) {
    await db.institutional_verifications.create({
      user_id,
      document_type,
      document_url: file_url,
      status: 'pending'
    })
    
    // Notify Admin
    await notifyAdminNewVerification(user_id)
    
    return {
      status: 'uploaded',
      message: 'Document uploaded successfully. Admin will review within 24-48h.',
      estimated_review_time: '24-48 hours'
    }
  }
}
```

**Chatbot-Dialoge:**

```
User: "Ich bin Polizist, bekomme ich Rabatt?"

AI: "Ja! Als Polizist erhalten Sie 10% institutionellen Rabatt zusätzlich 
     zu unserem Jahresrabatt (20%). Das sind insgesamt 30% Ersparnis!
     
     Um den Rabatt zu aktivieren, müssen Sie Ihre Zugehörigkeit nachweisen:
     
     ✅ Option 1: Laden Sie Ihren Dienstausweis hoch
     ✅ Option 2: Verwenden Sie Ihre Dienst-Email (@polizei.de)
     
     Möchten Sie jetzt starten?"

User: "Ja, wie lade ich den Dienstausweis hoch?"

AI: "Sie können direkt hier im Chat hochladen oder auf der Verification-Page.
     
     [UPLOAD_BUTTON: Dienstausweis hochladen]
     [LINK: Zur Verification-Page]
     
     Akzeptierte Formate: PDF, JPG, PNG (max 10MB)
     Bearbeitungszeit: 24-48 Stunden"
```

---

### 6. ADMIN-VERIFICATION-WORKFLOW

**Admin-Panel: Verification-Queue**

```tsx
<VerificationQueue>
  <Filters>
    <Select label="Status">
      <Option value="pending">Pending (12)</Option>
      <Option value="approved">Approved (45)</Option>
      <Option value="rejected">Rejected (3)</Option>
    </Select>
    
    <Select label="Org Type">
      <Option value="all">All</Option>
      <Option value="police">Polizei (5)</Option>
      <Option value="detective">Detektive (4)</Option>
      <Option value="lawyer">Anwälte (3)</Option>
    </Select>
  </Filters>
  
  <Table>
    {verifications.map(v => (
      <Row key={v.id}>
        <Cell>{v.user.username}</Cell>
        <Cell>{v.user.email}</Cell>
        <Cell>{v.organization_type}</Cell>
        <Cell>{v.organization_name}</Cell>
        <Cell>
          {v.documents.map(doc => (
            <DocumentPreview 
              url={doc.url} 
              type={doc.type}
              onView={openInNewTab}
            />
          ))}
        </Cell>
        <Cell>
          <Button onClick={() => approve(v.id)} color="green">
            ✅ Approve
          </Button>
          <Button onClick={() => reject(v.id)} color="red">
            ❌ Reject
          </Button>
          <Button onClick={() => requestMoreInfo(v.id)} color="blue">
            💬 More Info
          </Button>
        </Cell>
      </Row>
    ))}
  </Table>
</VerificationQueue>
```

**Approval-Flow:**

```typescript
async function approveVerification(verification_id: number, admin_id: number) {
  const verification = await db.institutional_verifications.findById(verification_id)
  
  // Update Verification
  await db.institutional_verifications.update(verification_id, {
    status: 'approved',
    reviewed_by: admin_id,
    reviewed_at: new Date()
  })
  
  // Update User
  await db.users.update(verification.user_id, {
    institutional_discount_verified: true,
    verification_status: 'approved',
    verified_at: new Date(),
    verified_by: admin_id
  })
  
  // Send Success Email
  await sendEmail({
    to: verification.user.email,
    subject: '🎉 Institutional Discount Approved!',
    template: 'verification_approved',
    data: {
      organization_type: verification.organization_type,
      discount_amount: '10%',
      total_savings: calculateSavings(verification.user)
    }
  })
  
  // Notify Chatbot (in-app notification)
  await createNotification({
    user_id: verification.user_id,
    type: 'verification_approved',
    title: 'Institutional Discount Activated!',
    message: 'You now receive 10% off all plans. Total savings: 30% with annual billing!'
  })
}
```

---

### 7. MARKETING-INTEGRATION

**Pricing-Page Messaging:**

```tsx
<InstitutionalDiscountBanner>
  <Icon>🏛️</Icon>
  <Title>Institutional Discount Available</Title>
  <Description>
    Police, Detectives, Lawyers, and Government agencies 
    receive an additional 10% discount.
  </Description>
  
  <Benefits>
    <Benefit>
      <Check>✅</Check>
      20% annual discount
    </Benefit>
    <Benefit>
      <Check>✅</Check>
      +10% institutional discount
    </Benefit>
    <Benefit>
      <Strong>= 30% total savings</Strong>
    </Benefit>
  </Benefits>
  
  <CTA>
    <Link to="/register?institutional=true">
      Claim Your Institutional Discount
    </Link>
  </CTA>
</InstitutionalDiscountBanner>
```

**Use-Case-Pages Integration:**

Auf jeder Use-Case-Page (Polizei, Detektive, Anwälte):

```tsx
<PricingSection>
  <Headline>Special Pricing for {useCase.title}</Headline>
  
  <PriceComparison>
    <Column type="standard">
      <Label>Standard Price</Label>
      <Price>$99/month</Price>
      <Annual>$1,188/year</Annual>
    </Column>
    
    <Column type="institutional" highlighted>
      <Badge>🏛️ Institutional</Badge>
      <Label>Your Price</Label>
      <Price strikethrough>$99</Price>
      <Price>$71/month</Price>
      <Annual strikethrough>$1,188</Annual>
      <Annual>$855/year</Annual>
      <Savings>Save $333/year (28%)</Savings>
    </Column>
  </PriceComparison>
  
  <Requirements>
    <Title>Verification Required:</Title>
    <Requirement>✅ Valid police/detective/law ID</Requirement>
    <Requirement>✅ Official email (@polizei.de, etc.)</Requirement>
    <Requirement>✅ Business license (for agencies)</Requirement>
  </Requirements>
</PricingSection>
```

---

### 8. EMAIL-TEMPLATES

#### Template 1: Verification Started

```html
Subject: 🔐 Institutional Discount Verification Started

Hi {{username}},

Thank you for requesting institutional discount verification!

Organization Type: {{organization_type}}
Organization: {{organization_name}}

Next Steps:
1. Upload your verification documents
2. Admin review (24-48 hours)
3. Discount automatically activated

Upload Documents: {{upload_link}}

Questions? Reply to this email or chat with our AI assistant.

Best regards,
SIGMACODE Team
```

#### Template 2: Verification Approved

```html
Subject: 🎉 Institutional Discount Approved - 10% OFF!

Hi {{username}},

Great news! Your institutional verification has been approved.

✅ 10% Institutional Discount: ACTIVE
✅ 20% Annual Discount: Available
✅ Total Savings: Up to 30%

Your new pricing:
- Pro Plan: $71/month (was $99)
- Annual: $855/year (was $1,188)
- YOU SAVE: $333/year

Start saving now: {{pricing_link}}

Best regards,
SIGMACODE Team
```

---

## 📊 BUSINESS IMPACT

### Expected Results:

**Conversion-Rate:**
```
Ohne Institutional Discount:  15%
Mit Institutional Discount:   28% (+87%)

Reason: Klarer Value-Prop für Zielgruppe
```

**Customer Acquisition Cost:**
```
Standard CAC:        $450
Institutional CAC:   $280 (-38%)

Reason: Höhere Conversion durch Rabatt
```

**Lifetime Value:**
```
Standard LTV:        $3,600 (3 Jahre)
Institutional LTV:   $3,078 (3 Jahre, mit 30% Rabatt)

BUT: Höheres Volumen kompensiert niedrigeren Price
```

**Revenue-Impact (Year 1):**
```
Target: 500 Institutional Customers
Average Plan: Pro ($855/Jahr mit Rabatt)
Revenue: $427,500

Ohne Discount hätten wir nur 200 Kunden @ $1,188 = $237,600
NET GAIN: +$189,900 (+80%)
```

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: MVP (Week 1)
- [ ] User-Model erweitern (organization_type, etc.)
- [ ] Registration-Form mit Organization-Selection
- [ ] Billing-Logik für 10% Discount
- [ ] Basic Admin-Panel für Approval
- [ ] Email-Templates

### Phase 2: Automation (Week 2)
- [ ] Email-Domain Auto-Verification
- [ ] Document-Upload-System
- [ ] Chatbot-Tools (3 neue)
- [ ] In-App-Notifications

### Phase 3: Polish (Week 3)
- [ ] Use-Case-Pages Pricing-Integration
- [ ] Marketing-Materials
- [ ] Analytics-Tracking
- [ ] A/B-Testing Setup

---

## ✅ SUCCESS METRICS

**KPIs to Track:**
- Institutional Signup-Rate
- Verification-Request-Rate
- Approval-Rate
- Time-to-Verification
- Revenue from Institutional Customers
- Churn-Rate (Institutional vs. Standard)

**Target KPIs (6 Monate):**
```
Institutional Customers:  500
Verification-Rate:        80%
Approval-Rate:            90%
Avg. Review-Time:         < 24h
Revenue Impact:           +80%
```

---

**Status:** SPEC COMPLETE - Ready to Implement  
**Priority:** HIGH (hoher Business-Impact)  
**Timeline:** 3 Wochen (MVP → Production)
