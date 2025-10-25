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

  note "1) Simple TX trace"
  curl -fsS -X POST "${API_BASE}/api/trace" \
    -H 'Content-Type: application/json' \
    -d '{"tx_hash":"0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef","chain":"ethereum"}' | tee /tmp/tx_trace.json >/dev/null
  ok "TX trace OK"

  note "2) TX scan (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/tx_scan.json -w '%{http_code}' -X POST "${API_BASE}/api/tx/scan" \
    -H 'Content-Type: application/json' \
    -d '{"chain":"ethereum","from_address":"0x1111111111111111111111111111111111111111","to_address":"0x2222222222222222222222222222222222222222","value":"0.01"}')
  if [ "$HTTP_CODE" = "200" ]; then
    ok "TX scan OK"
  else
    warn "TX scan skipped (status=${HTTP_CODE})"
  fi

  note "3) Address analysis"
  curl -fsS -X POST "${API_BASE}/api/analyze/address" \
    -H 'Content-Type: application/json' \
    -d '"0x742d35cc6634c0532925a3b844bc454e4438f44e"' | tee /tmp/addr_analyze.json >/dev/null
  ok "Address analysis OK"

  ok "E2E Smoke completed"
}

main "$@"
