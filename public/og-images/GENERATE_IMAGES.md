# OpenGraph Images für Use Cases

## Benötigte Images (1200x630px):

### 1. use-case-police.png
**Titel:** "24/7 AI-Agents für Polizei"
**Subtitle:** "Automatische Blockchain-Überwachung in Echtzeit"
**Visuals:** 
- 🚔 Polizei-Badge Icon
- 🤖 AI-Agent Visualization
- 24/7 Clock
- Blue-Purple Gradient Background
- Network-Graph im Hintergrund

**Text on Image:**
```
24/7 AI-AGENTS FÜR POLIZEI
Automatische Blockchain-Überwachung
∞ Wallets | < 1s Alerts | 100% Automatisiert
```

---

### 2. use-case-investigators.png
**Titel:** "10x Umsatz für Detektive"
**Subtitle:** "AI ermittelt, während Sie akquirieren"
**Visuals:**
- 🔍 Lupe/Detective Icon
- 💰 Money/Revenue Growth Chart
- AI Brain
- Purple-Pink Gradient Background
- ROI-Graph: 10x Steigerung

**Text on Image:**
```
PRIVATDETEKTIVE: 10x UMSATZ MIT AI
Von 5 Fällen → 50 Fälle/Monat
Von $15k → $150k Monatsumsatz
60,000% ROI nachgewiesen
```

---

### 3. use-cases-overview.png
**Titel:** "Blockchain-Forensik für jeden Use Case"
**Subtitle:** "AI-powered für Polizei, Detektive, Anwälte, Compliance"
**Visuals:**
- 6 Icons für alle Zielgruppen (Grid)
- 🤖 AI-Badge in der Mitte
- Multi-color Gradient (Blue-Purple-Pink-Orange)
- Network connections zwischen Icons

**Text on Image:**
```
BLOCKCHAIN-FORENSIK
6 Use Cases | AI-Powered | Real-Time
Polizei • Detektive • Anwälte • Compliance
35+ Chains | < 1s Alerts | 24/7
```

---

## Design-Guidelines:

**Dimensions:** 1200x630px (OpenGraph Standard)

**Colors:**
- Primary: Blue (#3B82F6)
- Secondary: Purple (#8B5CF6)
- Accent: Pink (#EC4899)
- Background: Dark Gradient (#0F172A → #1E293B)

**Typography:**
- Title: Bold, 60-72px
- Subtitle: Medium, 36-48px
- Body: Regular, 24-32px
- Font: Inter or System Font

**Branding:**
- Logo: Bottom-right corner (small)
- URL: sigmacode.io (bottom)

**AI-Elements:**
- 🤖 AI-Badge prominent
- Neural Network Pattern (subtle)
- Animated-style elements (suggesting movement)

---

## Tools zum Erstellen:

### Option 1: Figma/Canva (Empfohlen)
1. Template 1200x630px erstellen
2. Gradient-Background
3. Icons von Lucide
4. Export als PNG

### Option 2: Code-Generator (Next.js API Route)
```tsx
// pages/api/og/[slug].tsx
import { ImageResponse } from '@vercel/og'

export default function handler(req) {
  const { slug } = req.query
  
  return new ImageResponse(
    <div style={{
      background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
      width: '100%',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      fontFamily: 'Inter',
    }}>
      <h1 style={{ fontSize: 72, fontWeight: 'bold', color: 'white' }}>
        {getTitleForSlug(slug)}
      </h1>
    </div>,
    { width: 1200, height: 630 }
  )
}
```

### Option 3: Photoshop/GIMP
- Template mit 1200x630px
- Gradient Layer
- Text Layers
- Icons als Shapes
- Export als PNG (optimiert)

---

## Wo die Images verwenden:

1. **Meta Tags:**
   ```tsx
   <meta property="og:image" content="/og-images/use-case-police.png" />
   <meta property="og:image:width" content="1200" />
   <meta property="og:image:height" content="630" />
   <meta name="twitter:card" content="summary_large_image" />
   <meta name="twitter:image" content="/og-images/use-case-police.png" />
   ```

2. **Social Media Preview:**
   - LinkedIn Posts
   - Twitter/X Cards
   - Facebook Posts
   - WhatsApp Previews

3. **Testing:**
   - Facebook Debugger: https://developers.facebook.com/tools/debug/
   - Twitter Card Validator: https://cards-dev.twitter.com/validator
   - LinkedIn Post Inspector: https://www.linkedin.com/post-inspector/

---

## Priorität:

1. ✅ **use-cases-overview.png** (Höchste - Haupt-Landing)
2. ✅ **use-case-police.png** (Hoch - Neue Zielgruppe)
3. ✅ **use-case-investigators.png** (Hoch - Neue Zielgruppe)

---

## Placeholder bis echte Images erstellt sind:

Für jetzt verwenden wir die bestehenden OG-Images als Fallback.
Die neuen Images sollten innerhalb 1-2 Tage erstellt werden.

**Temporäre Lösung:**
Alle Pages funktionieren auch ohne spezifische OG-Images.
Browser/Social Media zeigen dann den Title + Description.

---

**Status:** TODO - Images müssen noch erstellt werden
**Timeline:** 1-2 Tage
**Tools:** Figma + Photoshop
**Designer:** TBD
