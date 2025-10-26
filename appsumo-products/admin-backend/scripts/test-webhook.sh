#!/usr/bin/env bash
set -euo pipefail

API_BASE="${KPI_API_URL:-http://localhost:8000}"
SECRET="${APPSUMO_WEBHOOK_SECRET:-dev-secret}"

note() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
ok() { echo -e "\033[1;32m[OK]\033[0m  $*"; }
err() { echo -e "\033[1;31m[ERR]\033[0m  $*"; }

BODY='{
  "id": "evt_demo_001",
  "type": "activated",
  "data": {
    "email": "demo@appsumo.com",
    "product": "wallet-guardian",
    "tier": 2,
    "code": "APPSUMO-WALLETGUARDIAN-TIER2-ABCDE"
  }
}'

SIG_HEX=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')
SIG_HEADER="sha256=${SIG_HEX}"

note "POST ${API_BASE}/api/appsumo/webhooks"
HTTP_CODE=$(curl -sS -o /tmp/webhook_resp.json -w '%{http_code}' \
  -X POST "${API_BASE}/api/appsumo/webhooks" \
  -H "Content-Type: application/json" \
  -H "X-AppSumo-Signature: ${SIG_HEADER}" \
  --data "$BODY")

if [ "$HTTP_CODE" = "200" ]; then
  ok "Webhook accepted"
else
  err "Webhook failed (HTTP ${HTTP_CODE})"
  cat /tmp/webhook_resp.json || true
  exit 1
fi

note "Fetch KPIs"
curl -fsS "${API_BASE}/api/admin/kpis" | jq . 2>/dev/null || curl -fsS "${API_BASE}/api/admin/kpis" || true
ok "Done"
