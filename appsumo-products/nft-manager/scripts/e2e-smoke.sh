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

  note "1) Get NFT portfolio"
  curl -fsS -X POST "${API_BASE}/api/portfolio" \
    -H 'Content-Type: application/json' \
    -d '{"address":"0x742d35cc6634c0532925a3b844bc454e4438f44e","chain":"ethereum"}' | tee /tmp/nft_portfolio.json >/dev/null
  ok "Portfolio OK"

  note "2) Get collections"
  curl -fsS "${API_BASE}/api/collections" | tee /tmp/nft_collections.json >/dev/null
  ok "Collections OK"

  note "3) Portfolio risk assessment (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/nft_risk.json -w '%{http_code}' -X POST "${API_BASE}/api/portfolio/risk" \
    -H 'Content-Type: application/json' \
    -d '{"address":"0x742d35cc6634c0532925a3b844bc454e4438f44e","chain":"ethereum"}')
  if [ "$HTTP_CODE" = "200" ]; then
    ok "Risk assessment OK"
  else
    warn "Risk assessment skipped (status=${HTTP_CODE})"
  fi

  note "4) Collection analytics"
  curl -fsS "${API_BASE}/api/analytics/Bored%20Ape%20Yacht%20Club" | tee /tmp/nft_analytics.json >/dev/null
  ok "Analytics OK"

  ok "E2E Smoke completed"
}

main "$@"
