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

  note "1) Generate tax report"
  curl -fsS -X POST "${API_BASE}/api/generate-report" \
    -H 'Content-Type: application/json' \
    -d '{"wallet":"0x742d35cc6634c0532925a3b844bc454e4438f44e","year":2024,"jurisdiction":"US"}' >/dev/null
  ok "Tax report OK"

  note "2) Get jurisdictions"
  curl -fsS "${API_BASE}/api/jurisdictions" >/dev/null
  ok "Jurisdictions OK"

  ok "E2E Smoke completed"
}

main "$@"
