#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
TOKEN="${TOKEN:-$(cat ./token.txt 2>/dev/null || true)}"
ORG_ID="${ORG_ID:-$(cat ./org_id.txt 2>/dev/null || true)}"

hdr_auth=()
if [[ -n "${TOKEN}" ]]; then
  hdr_auth=(-H "Authorization: Bearer ${TOKEN}")
fi
hdr_org=()
if [[ -n "${ORG_ID}" ]]; then
  hdr_org=(-H "X-Org-Id: ${ORG_ID}")
fi

step() { echo -e "\n==> $*"; }
pass() { echo "✔ $*"; }
fail() { echo "✘ $*"; exit 1; }

step "Health"
curl -fsS "${API_BASE}/health" | jq . >/dev/null && pass "health ok"

step "List Orgs"
curl -fsS "${API_BASE}/api/v1/orgs" "${hdr_auth[@]}" | jq . >/dev/null && pass "orgs listed"

if [[ -n "${ORG_ID}" ]]; then
  step "Org-protected endpoint (graph stats)"
  curl -fsS "${API_BASE}/api/v1/graph-analytics/stats/network" "${hdr_auth[@]}" "${hdr_org[@]}" | jq . >/dev/null && pass "graph stats ok"
else
  echo "(skip org-protected: no ORG_ID provided)"
fi

step "Billing plans"
curl -fsS "${API_BASE}/api/v1/billing/plans" "${hdr_auth[@]}" | jq . >/dev/null && pass "plans ok"

step "Usage remaining"
resp=$(curl -fsS -D - "${API_BASE}/api/v1/billing/usage/remaining" "${hdr_auth[@]}" "${hdr_org[@]}" -o /dev/null)
echo "$resp" | grep -i "X-Usage-Plan" >/dev/null && pass "usage headers present" || fail "missing usage headers"

step "Privacy DSR export ticket"
curl -fsS -X GET "${API_BASE}/api/v1/privacy/me/export" "${hdr_auth[@]}" | jq . >/dev/null && pass "dsr export queued"

step "Rate limit check (graph/subgraph quick burst)"
code=0
for i in {1..35}; do
  curl -s -o /dev/null -w "%{http_code}\n" "${API_BASE}/api/v1/graph/subgraph?address=0x0" "${hdr_auth[@]}" "${hdr_org[@]}" || true
done | { grep -q "429" && pass "rate limit enforced" || echo "(no 429 observed in quick local run)"; }

echo -e "\nSmoke tests finished."
