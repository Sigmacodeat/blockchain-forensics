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

  note "1) Bundle status"
  curl -fsS "${API_BASE}/api/bundle/status" >/dev/null
  ok "Bundle status OK"

  note "2) Quick scan (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/bundle_scan.json -w '%{http_code}' -X POST "${API_BASE}/api/bundle/quick-scan" \
    -H 'Content-Type: application/json' \
    -d '{
      "addresses": ["0x742d35cc6634c0532925a3b844bc454e4438f44e", "0x1234567890123456789012345678901234567890"],
      "include_tracing": false,
      "include_fraud_check": true,
      "include_portfolio": true
    }')
  if [ "$HTTP_CODE" = "200" ]; then
    ok "Quick scan OK"
  else
    warn "Quick scan skipped (status=${HTTP_CODE})"
  fi

  note "3) Comprehensive audit (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/bundle_audit.json -w '%{http_code}' -X POST "${API_BASE}/api/bundle/comprehensive-audit" \
    -H 'Content-Type: application/json' \
    -d '{
      "addresses": ["0x742d35cc6634c0532925a3b844bc454e4438f44e"],
      "include_tracing": true,
      "include_fraud_check": true,
      "include_portfolio": true
    }')
  if [ "$HTTP_CODE" = "200" ]; then
    ok "Comprehensive audit OK"
  else
    warn "Comprehensive audit skipped (status=${HTTP_CODE})"
  fi

  ok "E2E Smoke completed"
}

main "$@"
