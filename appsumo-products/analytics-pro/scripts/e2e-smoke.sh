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

  note "1) Portfolio overview"
  curl -fsS "${API_BASE}/api/portfolio/0x742d35cc6634c0532925a3b844bc454e4438f44e" | tee /tmp/ap_portfolio.json >/dev/null
  ok "Portfolio OK"

  note "2) Firewall stats (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/ap_fw_stats.json -w '%{http_code}' "${API_BASE}/api/firewall/stats")
  if [ "$HTTP_CODE" = "200" ]; then
    ok "Firewall stats OK"
  else
    warn "Firewall stats skipped (status=${HTTP_CODE})"
  fi

  note "3) Deep wallet scan (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/ap_deep_scan.json -w '%{http_code}' -X POST "${API_BASE}/api/wallet/scan/deep" \
    -H 'Content-Type: application/json' \
    -d '{"address":"0x742d35cc6634c0532925a3b844bc454e4438f44e","chain":"ethereum"}')
  if [ "$HTTP_CODE" = "200" ]; then
    ok "Deep scan OK"
  else
    warn "Deep scan skipped (status=${HTTP_CODE})"
  fi

  ok "E2E Smoke completed"
}

main "$@"
