# 🚀 WALLET GUARDIAN - 5-MINUTE QUICK START

**Get protected in 5 minutes or less!**

---

## Step 1: Activate Your AppSumo Code (30 seconds)

1. Go to: https://blocksigmakode.ai/redeem/appsumo
2. Enter your AppSumo code
3. Create account (or login)
4. **Done!** ✅

Your account is now activated with your purchased tier.

---

## Step 2: Add Your First Wallet (1 minute)

### Option A: Auto-Connect (Recommended)
```
1. Click "Connect Wallet" button
2. Select MetaMask/TronLink/etc.
3. Approve connection
4. ✅ Protected automatically!
```

### Option B: Manual Entry
```
1. Dashboard → Settings → Wallets
2. Click "Add Wallet"
3. Enter address: 0x...
4. Click "Save"
5. ✅ Wallet added!
```

---

## Step 3: Configure Protection (2 minutes)

### Basic Protection (Default)
Already enabled! You're protected against:
- ✅ Token approval scams
- ✅ Phishing sites
- ✅ Malicious contracts
- ✅ Sanctions addresses
- ✅ Known scammers

### Advanced Protection (Optional)
```
Dashboard → Rules → Create Custom Rule

Example: Block all transactions > $10,000
- Trigger: Transaction Amount
- Condition: Greater than
- Value: 10000
- Action: Block & Alert
```

---

## Step 4: Enable Alerts (1 minute)

### Email Alerts (Free)
```
Dashboard → Settings → Notifications
✅ Enable email alerts
Enter email: your@email.com
✅ Save
```

### SMS Alerts (Tier 2+)
```
Dashboard → Settings → Notifications
✅ Enable SMS alerts
Enter phone: +1234567890
✅ Save
```

### Discord/Telegram (Tier 3)
```
Dashboard → Integrations
Select: Discord or Telegram
Click: Connect
Authorize
```

---

## Step 5: Test Protection (1 minute)

### Test Transaction
```
1. Dashboard → Test Center
2. Click "Run Safety Test"
3. Wait 10 seconds...
4. See results!

You should see:
- All 15 ML models active
- 7 defense layers working
- Response time < 100ms
```

---

## Optional: Connect to Main Backend (Deep Protection)

Enable proxy to the main platform for real AI/Forensics:

1) Set env in `backend/.env` (or export before `docker-compose up`):
```
MAIN_BACKEND_URL=http://host.docker.internal:8000
# Optional if main backend protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Endpoints available via Wallet Guardian:
```
POST  /api/scan/deep            # Address deep scan (forensics-backed)
POST  /api/tx/scan              # AI Firewall transaction scan
POST  /api/trace/start          # Start forensic trace
GET   /api/trace/{id}/report    # Download JSON/CSV/PDF report
```

3) Frontend additions on Dashboard:
- Transaction Scanner (uses /api/tx/scan)
- Forensic Trace (start + download report)
- Wallet Scanner „Deep Scan“ Toggle

Notes:
- If `MAIN_BACKEND_URL` is not set, Wallet Guardian falls back to local mock scan.
- In master compose, the guardian backend runs on `8002` and frontend uses `VITE_API_URL=http://localhost:8002`.

---

## YOU'RE PROTECTED!

Your wallet is now protected 24/7 by:
- 15 AI models
- 7 defense layers
- Real-time scanning
- Instant alerts

---

## 📱 NEXT STEPS

### Install Browser Extension (Coming Soon)
- Chrome, Firefox, Brave support
- One-click protection
- No configuration needed

### Mobile App (Coming Q1 2026)
- iOS + Android
- Push notifications
- Biometric auth

### API Integration (Tier 3)
```bash
curl -X POST https://api.blocksigmakode.ai/v1/firewall/scan \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "ethereum",
    "from": "0x...",
    "to": "0x...",
    "value": "1000000000000000000"
  }'
```

---

## 🆘 NEED HELP?

### Quick Fixes

**Problem**: Not receiving alerts
**Solution**: Check spam folder, verify email/phone

**Problem**: False positive (legit transaction blocked)
**Solution**: Dashboard → History → Click transaction → "Mark as Safe"

**Problem**: Slow response
**Solution**: Check internet connection, try different RPC

### Support Channels

- **Email**: support@blocksigmakode.ai (24-48h)
- **Discord**: https://discord.gg/blocksigmakode (Live chat)
- **Docs**: https://docs.blocksigmakode.ai/wallet-guardian
- **Status**: https://status.blocksigmakode.ai

---

## 📊 USAGE TIPS

### Best Practices
1. ✅ **Enable all alert channels** (Email + SMS + Discord)
2. ✅ **Review blocked transactions daily**
3. ✅ **Update whitelist/blacklist weekly**
4. ✅ **Run safety tests before large transfers**
5. ✅ **Keep API key secure** (Tier 3 only)

### Common Scenarios

**Scenario**: Trading on Uniswap
- Auto-approved: Safe contracts whitelisted
- Alert: High gas fees (warning only)

**Scenario**: Claiming airdrop
- Checked: Token contract safety
- Blocked: If approval unlimited
- Recommended: Manual approval with limit

**Scenario**: Sending to new address
- Checked: Address reputation
- Alert: If first-time recipient
- Warning: If high-risk cluster

---

## 🎓 LEARN MORE

### Video Tutorials (2-5 min each)
- Getting Started: https://youtube.com/watch?v=...
- Advanced Rules: https://youtube.com/watch?v=...
- API Integration: https://youtube.com/watch?v=...

### Blog Posts
- "Top 10 Crypto Scams in 2025"
- "Understanding Token Approvals"
- "How We Detect Phishing Sites"

### Webinars (Live)
- Every Tuesday: Security Q&A
- Every Thursday: Feature Deep-Dive
- Monthly: Threat Landscape Update

---

## 💎 UPGRADE ANYTIME

### Current Tier Features
Check your tier: Dashboard → Account → Subscription

### Upgrade Options
- **Tier 1 → Tier 2**: $70 (pay difference)
- **Tier 2 → Tier 3**: $100 (pay difference)
- **Lifetime Access**: No recurring fees

---

**Protected since**: [Today's date]  
**Scans performed**: 0 (starts now!)  
**Threats blocked**: 0 (hopefully stays that way!)

**Stay safe! 🛡️**
