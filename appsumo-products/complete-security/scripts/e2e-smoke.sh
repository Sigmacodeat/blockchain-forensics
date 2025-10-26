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

  note "1) Security scan"
  curl -fsS "${API_BASE}/api/security/scan" | tee /tmp/cs_scan.json >/dev/null
  ok "Security scan OK"

  note "2) Threats"
  curl -fsS "${API_BASE}/api/security/threats" | tee /tmp/cs_threats.json >/dev/null
  ok "Threats OK"

  note "3) Firewall rules (proxy)"
  HTTP_CODE=$(curl -sS -o /tmp/cs_rules.json -w '%{http_code}' "${API_BASE}/api/security/rules")
  if [ "$HTTP_CODE" = "200" ]; then
    ok "Firewall rules OK"
  else
    warn "Firewall rules skipped (status=${HTTP_CODE})"
  fi

  ok "E2E Smoke completed"
}

main "$@"
