# Analytics & Attribution Implementation

## 1. GA4 + Plausible Setup

### GA4 Implementation (gtag)
```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID', {
    'custom_map': {'dimension1': 'user_tier'},
    'send_page_view': true
  });
</script>

<!-- Plausible Analytics -->
<script defer data-domain="blockchain-forensics.com" src="https://plausible.io/js/script.js"></script>
```

### Server-Side Events (Reliability)
```javascript
// Send events server-side for critical conversions
async function trackConversion(eventName, data) {
  try {
    await fetch('/api/analytics/track', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: eventName,
        data: data,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        referrer: document.referrer
      })
    });
  } catch (e) {
    console.error('Server-side tracking failed:', e);
  }
}
```

## 2. UTM Conventions for AppSumo

### AppSumo Traffic Attribution
```
?utm_source=appsumo
&utm_medium=cpc
&utm_campaign=lifetime-deals
&utm_content={product-slug}
&utm_term={tier}
```

### Examples:
- `https://domain.com/products/wallet-guardian?utm_source=appsumo&utm_medium=cpc&utm_campaign=lifetime-deals&utm_content=wallet-guardian&utm_term=tier1`
- `https://domain.com/products/analytics-pro?utm_source=appsumo&utm_medium=cpc&utm_campaign=lifetime-deals&utm_content=analytics-pro&utm_term=tier2`

### Auto-UTM for AppSumo Links
```javascript
function addAppSumoUTM(url, productSlug, tier) {
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}utm_source=appsumo&utm_medium=cpc&utm_campaign=lifetime-deals&utm_content=${productSlug}&utm_term=${tier}`;
}
```

## 3. Conversion Events

### Critical Events to Track
```javascript
// License Activation (Primary Conversion)
gtag('event', 'license_activated', {
  'event_category': 'conversion',
  'event_label': 'appsumo',
  'value': tier_price,
  'custom_parameter_1': product_slug,
  'custom_parameter_2': tier
});

// Feature Usage Events
gtag('event', 'feature_used', {
  'event_category': 'engagement',
  'event_label': feature_name,
  'custom_parameter_1': product_slug
});

// Upgrade Events
gtag('event', 'tier_upgrade', {
  'event_category': 'conversion',
  'event_label': 'upsell',
  'value': upgrade_price
});
```

### Server-Side Conversion Tracking
```python
@app.post("/api/analytics/track")
async def track_event(request: Request):
    data = await request.json()
    event_name = data.get("event")

    # Store in database for analysis
    db_event = AnalyticsEvent(
        event_name=event_name,
        data=json.dumps(data),
        ip=request.client.host,
        user_agent=data.get("userAgent"),
        timestamp=datetime.utcnow()
    )
    db.add(db_event)
    db.commit()

    # Forward to external analytics if needed
    return {"status": "tracked"}
```

## 4. Attribution Setup

### Multi-Touch Attribution Model
- **First-Touch**: Initial discovery (organic search, social)
- **Last-Touch**: Final conversion (AppSumo purchase)
- **Linear**: Equal credit across all touchpoints

### Attribution Windows
- **View-Through**: 30 days for display ads
- **Click-Through**: 90 days for paid search
- **Post-Conversion**: Track upsells and referrals

### Cross-Device Tracking
```javascript
// User ID persistence across devices
function getOrCreateUserId() {
  let userId = localStorage.getItem('bf_user_id');
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem('bf_user_id', userId);
  }
  return userId;
}

// Send user ID with all events
gtag('config', 'GA_MEASUREMENT_ID', {
  'user_id': getOrCreateUserId()
});
```

## 5. Privacy & Compliance

### GDPR Compliance
```javascript
// Consent management
function checkConsent() {
  return localStorage.getItem('analytics_consent') === 'granted';
}

function requestConsent() {
  // Show consent banner
  // Set localStorage on acceptance
}

// Only load analytics if consented
if (checkConsent()) {
  loadGoogleAnalytics();
  loadPlausible();
}
```

### Data Retention
- GA4: 26 months default
- Plausible: Configurable (default 12 months)
- Custom events: 2 years for analysis, then aggregate

## 6. Implementation Checklist

### GA4 Setup
- [ ] GA4 property created
- [ ] Custom dimensions configured (user_tier, product_slug)
- [ ] Conversion events set up
- [ ] Cross-domain tracking configured
- [ ] Enhanced ecommerce enabled

### Plausible Setup
- [ ] Domain configured
- [ ] Custom events set up
- [ ] Goal tracking configured
- [ ] Privacy-friendly settings enabled

### Server-Side Tracking
- [ ] `/api/analytics/track` endpoint implemented
- [ ] Event storage in database
- [ ] Error handling and retries
- [ ] Rate limiting implemented

### Attribution
- [ ] UTM parameter standardization
- [ ] Cross-device tracking enabled
- [ ] Attribution models configured
- [ ] Touchpoint mapping complete

### Privacy
- [ ] Consent banner implemented
- [ ] GDPR compliance verified
- [ ] Data retention policies set
- [ ] Cookie management configured

## 7. Monitoring & Reporting

### Dashboards to Create
1. **Traffic Overview**: Source/medium breakdown
2. **Conversion Funnel**: Visit → Interest → Trial → Purchase
3. **Attribution Report**: Channel contribution to conversions
4. **User Journey**: Path analysis before purchase
5. **Cohort Analysis**: User behavior over time

### Key Metrics to Track
- **Traffic**: Sessions, users, bounce rate, session duration
- **Engagement**: Page views, feature usage, time on page
- **Conversions**: License activations, tier upgrades, referrals
- **Revenue**: LTV, ARPU, churn rate, expansion revenue
- **Attribution**: Channel ROI, assisted conversions, multi-touch credit

### Alert System
- Traffic drops >20%
- Conversion rate changes >15%
- Revenue anomalies
- Technical issues (tracking failures)
