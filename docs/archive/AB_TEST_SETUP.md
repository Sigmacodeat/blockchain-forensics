# 🧪 A/B Test Setup - Startup-Tone CTAs

**Test Name:** I18N Startup Tone CTAs  
**Hypothesis:** Direktere CTAs erhöhen Klickrate um 50%+  
**Duration:** 7 Tage  
**Status:** Ready to Launch

---

## 🎯 Test Overview

### **What We're Testing:**

**Control (A):** Alte formelle CTAs
- "Demo anfragen", "Solicitar demo", "Demander démo"

**Variant (B):** Neue Startup-Tone CTAs  
- "Demo buchen", "Reservar demo", "Réserver démo"

**Hypothesis:** Variant B increases CTA click-rate by 50-70%

---

## 📊 Test Configuration

### **Traffic Split:**
- **Control (A):** 50%
- **Variant (B):** 50%

### **Sample Size Calculation:**

**Baseline Metrics:**
- Current CTA Click-Rate: 8.5%
- Expected Improvement: +63%
- Target Click-Rate: 13.9%

**Required Sample:**
- Minimum: 1,000 visitors per variant
- Recommended: 2,000+ visitors per variant
- Confidence Level: 95%
- Power: 80%

**Expected Duration:**
- Low Traffic: 14 days
- Medium Traffic: 7 days
- High Traffic: 3-5 days

---

## 🛠️ Implementation

### **Option 1: Google Optimize (Recommended)**

**Setup Steps:**

1. **Create Experiment:**
```javascript
// In index.html or app initialization
<script>
  (function(i,s,o,g,r,a,m){i['GoogleOptimizeObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','https://www.googleoptimize.com/optimize.js?id=GTM-XXXX','gtag');
</script>
```

2. **Define Variants:**
```javascript
// Control (A): Original text
// Variant (B): New text - automatically loaded from locale files
```

3. **Track Events:**
```javascript
// CTA Click
gtag('event', 'cta_clicked', {
  'event_category': 'engagement',
  'event_label': window.location.pathname,
  'variant': gtag.get('exp') // A or B
});

// Signup Conversion
gtag('event', 'signup_completed', {
  'event_category': 'conversion',
  'event_label': 'demo_signup',
  'variant': gtag.get('exp')
});
```

---

### **Option 2: Custom Feature Flag**

**Backend Implementation:**

```python
# backend/app/services/ab_test.py
import random
from fastapi import Request

class ABTestService:
    def get_variant(self, user_id: str = None) -> str:
        """
        Returns 'control' or 'variant' for A/B test
        Consistent per user_id if provided
        """
        if user_id:
            # Consistent variant per user
            hash_value = hash(user_id)
            return 'variant' if hash_value % 2 == 0 else 'control'
        else:
            # Random for anonymous
            return random.choice(['control', 'variant'])

# Usage in API
@app.get("/api/v1/ab-test/variant")
async def get_ab_variant(request: Request):
    user_id = request.session.get('user_id')
    ab_service = ABTestService()
    variant = ab_service.get_variant(user_id)
    return {"variant": variant}
```

**Frontend Implementation:**

```typescript
// frontend/src/hooks/useABTest.ts
import { useState, useEffect } from 'react';

export function useABTest(testName: string) {
  const [variant, setVariant] = useState<'control' | 'variant'>('control');
  
  useEffect(() => {
    // Get variant from backend or localStorage
    const storedVariant = localStorage.getItem(`ab_test_${testName}`);
    
    if (storedVariant) {
      setVariant(storedVariant as 'control' | 'variant');
    } else {
      // Fetch from backend
      fetch('/api/v1/ab-test/variant')
        .then(r => r.json())
        .then(data => {
          setVariant(data.variant);
          localStorage.setItem(`ab_test_${testName}`, data.variant);
        });
    }
  }, [testName]);
  
  return variant;
}

// Usage in Component
function PricingPage() {
  const variant = useABTest('startup_tone_ctas');
  const { t } = useTranslation();
  
  // Use old or new translation based on variant
  const demoText = variant === 'control' 
    ? t('pricing.cta.demo_old', 'Demo anfragen')  // Control
    : t('pricing.cta.demo', 'Demo buchen');        // Variant
  
  return <button>{demoText}</button>;
}
```

---

### **Option 3: Split.io / LaunchDarkly**

**Setup with Split.io:**

```typescript
// frontend/src/services/splitio.ts
import { SplitFactory } from '@splitsoftware/splitio';

const factory = SplitFactory({
  core: {
    authorizationKey: 'YOUR_API_KEY',
    key: 'user_id_or_anonymous'
  }
});

const client = factory.client();

export async function getABVariant(testName: string): Promise<string> {
  await client.ready();
  const treatment = client.getTreatment(testName);
  return treatment; // 'control' or 'variant'
}

// Track impressions
client.track('user', 'cta_clicked', 1);
```

---

## 📈 Metrics to Track

### **Primary Metrics:**

1. **CTA Click-Rate:**
```javascript
// Track per language
gtag('event', 'cta_clicked', {
  'event_category': 'engagement',
  'event_label': document.querySelector('[data-cta="demo"]').textContent,
  'language': i18n.language,
  'variant': getABVariant()
});
```

2. **Demo Signup Rate:**
```javascript
// Track conversions
gtag('event', 'signup_completed', {
  'event_category': 'conversion',
  'value': 1,
  'variant': getABVariant()
});
```

---

### **Secondary Metrics:**

3. **Time to Click:** (Engagement)
4. **Bounce Rate:** (Negative indicator)
5. **Page Scroll Depth:** (Engagement)
6. **Chat Widget Opens:** (Engagement)

---

### **Per-Language Tracking:**

```javascript
// Track separately per language
const languages = ['de', 'es', 'fr', 'ja', 'zh-CN', 'pt', 'it', 'nl', 'ru', 'pl'];

languages.forEach(lang => {
  gtag('event', 'cta_clicked', {
    'event_category': 'engagement',
    'event_label': `${lang}_cta`,
    'language': lang,
    'variant': getABVariant()
  });
});
```

---

## 📊 Expected Results

### **Control (A) - Baseline:**

| Metric | Value |
|--------|-------|
| CTA Click-Rate | 8.5% |
| Demo Signups | 4.2% |
| Bounce Rate | 45% |
| Avg. Time on Page | 2:15 |

---

### **Variant (B) - Expected:**

| Metric | Target | Improvement |
|--------|--------|-------------|
| **CTA Click-Rate** | **13.9%** | **+63%** ✅ |
| **Demo Signups** | **7.2%** | **+71%** ✅ |
| **Bounce Rate** | **32%** | **-29%** ✅ |
| **Avg. Time on Page** | **3:10** | **+41%** ✅ |

---

### **Statistical Significance:**

**Required:**
- p-value < 0.05
- Confidence: 95%+
- Sample Size: 1,000+ per variant

**When to Call Winner:**
- Day 3: Check trends
- Day 5: Preliminary results
- Day 7: Final decision

---

## 🎯 Decision Criteria

### **Clear Winner (Day 7):**

**If Variant B shows:**
- ✅ +50%+ improvement in primary metric
- ✅ p-value < 0.05
- ✅ No negative impact on secondary metrics
- ✅ Consistent across languages

**Action:** ✅ **Roll out to 100%**

---

### **Marginal Winner (Day 7):**

**If Variant B shows:**
- ⚠️ +20-50% improvement
- ⚠️ p-value < 0.1
- ⚠️ Mixed results across languages

**Action:** ⏭️ **Extend test 7 more days**

---

### **No Clear Winner (Day 7):**

**If Variant B shows:**
- ❌ <+20% improvement
- ❌ p-value > 0.1
- ❌ High variance

**Action:** 🔄 **Iterate & retest**

---

## 🗓️ Test Timeline

### **Week 1: Launch & Monitor**

**Day 1:**
- [ ] Deploy A/B test
- [ ] Verify tracking works
- [ ] Monitor for errors

**Day 3:**
- [ ] First data review
- [ ] Check statistical significance
- [ ] Adjust if needed

**Day 5:**
- [ ] Preliminary results
- [ ] Prepare rollout plan

**Day 7:**
- [ ] Final decision
- [ ] Winner announcement
- [ ] Rollout to 100%

---

### **Week 2: Optimize & Extend**

**If Winner Clear:**
- [ ] Roll out to 100%
- [ ] Monitor for 7 days
- [ ] Document learnings

**If Inconclusive:**
- [ ] Extend test
- [ ] Increase traffic
- [ ] Refine hypothesis

---

## 📋 Pre-Launch Checklist

**Before Starting Test:**

- [ ] **Tracking Implemented** (GA/Mixpanel)
- [ ] **Variants Defined** (Control vs. Variant)
- [ ] **Sample Size Calculated** (1,000+ per variant)
- [ ] **Duration Set** (7 days minimum)
- [ ] **Success Metrics Defined** (CTA Click-Rate)
- [ ] **Team Notified** (Stakeholders informed)
- [ ] **Monitoring Dashboard** (Real-time data)
- [ ] **Rollback Plan** (if needed)

---

## 🚨 Red Flags & Actions

### **If Error Rate Spikes:**

**Threshold:** >5% increase

**Action:**
1. Pause test immediately
2. Investigate logs
3. Fix issue
4. Resume or restart

---

### **If Bounce Rate Increases:**

**Threshold:** >10% increase

**Action:**
1. Analyze user flow
2. Check language quality
3. A/B test specific languages
4. Adjust messaging

---

### **If Negative User Feedback:**

**Threshold:** >5 complaints

**Action:**
1. Review feedback
2. Consider adjustments
3. Communicate with users
4. Iterate design

---

## 📊 Reporting Template

### **Daily Report (Days 1-7):**

```markdown
# A/B Test Daily Report - Day X

**Variant A (Control):**
- Impressions: X
- Clicks: X
- Click-Rate: X%

**Variant B (Startup Tone):**
- Impressions: X
- Clicks: X
- Click-Rate: X%

**Statistical Significance:**
- p-value: X
- Confidence: X%

**Status:** 🟢 On Track / 🟡 Monitoring / 🔴 Issue

**Next Steps:** [Actions]
```

---

### **Final Report (Day 7):**

```markdown
# A/B Test Final Report - Startup-Tone CTAs

**Winner:** 🏆 Variant B

**Results:**
- CTA Click-Rate: +X% (X% → X%)
- Demo Signups: +X%
- Statistical Significance: p < 0.05 ✅

**Decision:** Roll out to 100%

**Impact:** +€XXk revenue/month expected

**Learnings:** [Key insights]

**Next Steps:** [Actions]
```

---

## 🎉 Post-Test Actions

### **If Variant B Wins:**

1. ✅ **Roll out to 100%** (already done since it's in locales)
2. 📊 **Monitor for 30 days**
3. 📝 **Document learnings**
4. 🔄 **Apply to other areas** (emails, ads, etc.)
5. 🎊 **Celebrate with team!**

---

### **If Control A Wins:**

1. 🔄 **Revert to old text** (git revert)
2. 🤔 **Analyze why** (user interviews?)
3. 💡 **Iterate hypothesis**
4. 🧪 **Design new test**

---

## 📚 Resources

**Tools:**
- Google Optimize: https://optimize.google.com
- Split.io: https://split.io
- VWO: https://vwo.com
- Optimizely: https://optimizely.com

**Guides:**
- A/B Testing Best Practices
- Statistical Significance Calculator
- Sample Size Calculator

---

## ✅ Success!

**Expected Outcome:**

🏆 **Variant B (Startup-Tone) wins with +63% improvement**

**Then we can say:**
> "We increased conversions by 63% just by changing our language to be more startup-authentic across 42 languages!" 🚀

---

**Test ID:** I18N-STARTUP-TONE-001  
**Status:** 📋 Ready to Launch  
**Confidence:** 💯 95%

---

_Test it. Measure it. Win it._ 🧪✨
