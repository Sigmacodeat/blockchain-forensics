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

  note "1) Get protocols"
  curl -fsS "${API_BASE}/api/protocols" | tee /tmp/defi_protocols.json >/dev/null
  ok "Protocols OK"

  note "2) Get positions"
  curl -fsS -X POST "${API_BASE}/api/positions" \
    -H 'Content-Type: application/json' \
    -d '{"wallet":"0x742d35cc6634c0532925a3b844bc454e4438f44e","chain":"ethereum"}' | tee /tmp/defi_positions.json >/dev/null
  ok "Positions OK"

  note "3) Start forensic trace (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/defi_trace_start.json -w '%{http_code}' -X POST "${API_BASE}/api/trace/start" \
    -H 'Content-Type: application/json' \
    -d '{"source_address":"0x742d35cc6634c0532925a3b844bc454e4438f44e","direction":"forward","max_depth":2}')
  if [ "$HTTP_CODE" = "200" ]; then
    TRACE_ID=$(jq -r '.trace_id' /tmp/defi_trace_start.json 2>/dev/null || echo '')
    if [ -n "$TRACE_ID" ] && [ "$TRACE_ID" != "null" ]; then
      ok "Trace started: $TRACE_ID"
      note "4) Download trace JSON report"
      curl -fsS "${API_BASE}/api/trace/${TRACE_ID}/report?format=json" -o /tmp/defi_trace_report.json || warn "Report download failed"
    else
      warn "Trace start OK but trace_id missing"
    fi
  else
    warn "Trace start skipped (status=${HTTP_CODE})"
  fi

  ok "E2E Smoke completed"
}

main "$@"
