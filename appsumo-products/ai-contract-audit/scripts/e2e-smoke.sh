#!/usr/bin/env bash
set -euo pipefail

API_BASE="${VITE_API_URL:-${API_BASE:-http://localhost:8000}}"

note() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
ok() { echo -e "\033[1;32m[OK]\033[0m  $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[1;31m[ERR]\033[0m  $*"; }

wait_health() {
  local url="$1"; local i=0
  note "Waiting for backend health at ${url}/health ..."
  until curl -fsS "${url}/health" >/dev/null 2>&1; do
    i=$((i+1))
    if [ $i -gt 60 ]; then err "Health check timeout"; exit 1; fi
    sleep 1
  done
  ok "Backend healthy"
}

main() {
  note "API_BASE=${API_BASE}"
  wait_health "${API_BASE}"

  note "1) Contract audit (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/audit_result.json -w '%{http_code}' -X POST "${API_BASE}/api/audit/contract" \
    -H 'Content-Type: application/json' \
    -d '{
      "contract_address": "0x742d35cc6634c0532925a3b844bc454e4438f44e",
      "chain": "ethereum",
      "check_security": true,
      "check_gas_optimization": true,
      "check_vulnerabilities": true
    }')
  if [ "$HTTP_CODE" = "200" ]; then
    RISK_SCORE=$(jq -r '.overall_risk_score' /tmp/audit_result.json 2>/dev/null || echo "0")
    VULNS=$(jq -r '.vulnerabilities_found' /tmp/audit_result.json 2>/dev/null || echo "0")
    ok "Contract audit OK - Risk Score: ${RISK_SCORE}, Vulnerabilities: ${VULNS}"
  else
    warn "Contract audit skipped (status=${HTTP_CODE})"
  fi

  note "2) Audit history"
  curl -fsS "${API_BASE}/api/audit/history" >/dev/null
  ok "Audit history OK"

  note "3) Platform stats"
  curl -fsS "${API_BASE}/api/stats" >/dev/null
  ok "Platform stats OK"

  ok "E2E Smoke completed"
}

main "$@"
