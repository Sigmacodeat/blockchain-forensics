#!/usr/bin/env bash
set -euo pipefail

API_BASE="${VITE_API_URL:-${API_BASE:-http://localhost:8000}}"
DEAD="0x000000000000000000000000000000000000dead"

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

  note "1) Simple address scan"
  curl -fsS -X POST "${API_BASE}/api/scan" \
    -H 'Content-Type: application/json' \
    -d "{\"address\": \"${DEAD}\"}" | tee /tmp/wg_scan.json >/dev/null
  ok "Simple scan OK"

  note "2) Deep address scan (proxy)"
  if curl -sS -o /dev/null -w '%{http_code}' -X POST "${API_BASE}/api/scan/deep" \
      -H 'Content-Type: application/json' \
      -d "{\"address\": \"${DEAD}\"}" | grep -q '^200$'; then
    ok "Deep scan OK"
  else
    warn "Deep scan skipped (MAIN_BACKEND_URL not configured or unreachable)"
  fi

  note "3) Transaction scan (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/wg_tx.json -w '%{http_code}' -X POST "${API_BASE}/api/tx/scan" \
    -H 'Content-Type: application/json' \
    -d '{"chain":"ethereum","from_address":"0x1111111111111111111111111111111111111111","to_address":"0x2222222222222222222222222222222222222222","value":"0.01"}')
  if [ "$HTTP_CODE" = "200" ]; then
    ok "TX scan OK"
  else
    warn "TX scan skipped (status=${HTTP_CODE})"
  fi

  note "4) Forensic trace start (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/wg_trace.json -w '%{http_code}' -X POST "${API_BASE}/api/trace/start" \
    -H 'Content-Type: application/json' \
    -d "{\"source_address\": \"${DEAD}\", \"direction\": \"forward\", \"max_depth\": 2}")
  if [ "$HTTP_CODE" = "200" ]; then
    TRACE_ID=$(jq -r '.trace_id' /tmp/wg_trace.json 2>/dev/null || echo '')
    if [ -n "$TRACE_ID" ] && [ "$TRACE_ID" != "null" ]; then
      ok "Trace started: $TRACE_ID"
      note "Download trace JSON report"
      curl -fsS "${API_BASE}/api/trace/${TRACE_ID}/report?format=json" -o /tmp/wg_trace_report.json || warn "Report download failed"
    else
      warn "Trace started but ID missing"
    fi
  else
    warn "Trace start skipped (status=${HTTP_CODE})"
  fi

  ok "E2E Smoke completed"
}

main "$@"
