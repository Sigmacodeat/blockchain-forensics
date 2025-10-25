#!/usr/bin/env bash
set -euo pipefail

#
# KYT Rule Seeder (State-of-the-Art)
# - CLI-Flags: --base-url, --token, --dry-run
# - Validiert Regeln über /api/v1/monitor/rules/validate (falls verfügbar)
# - Pretty-Output via jq (falls vorhanden)
# - Robust gegen Fehler, klare Logs
#

BASE_URL=${BASE_URL:-http://localhost:8000}
TOKEN=${TOKEN:-}
DRY_RUN=${DRY_RUN:-0}

usage() {
  cat <<EOF
Usage: $0 [--base-url URL] [--token TOKEN] [--dry-run]

Environment overrides:
  BASE_URL   Backend Base URL (default: http://localhost:8000)
  TOKEN      Bearer token for auth (optional)
  DRY_RUN    1 to only validate and print payloads, do not create (default: 0)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="$2"; shift 2;;
    --token)
      TOKEN="$2"; shift 2;;
    --dry-run)
      DRY_RUN=1; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

API_RULES="${BASE_URL}/api/v1/monitor/rules"
API_VALIDATE="${BASE_URL}/api/v1/monitor/rules/validate"


have_jq=0
if command -v jq >/dev/null 2>&1; then have_jq=1; fi

log() { echo -e "[seed] $*"; }

validate_rule() {
  local name="$1"; shift
  local scope="$1"; shift
  local severity="$1"; shift
  local enabled=true
  local expression_json="$1"
  # Validate payload
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "DRY-RUN validate -> name='${name}', scope='${scope}', severity='${severity}'"
    return 0
  fi
  local http_code
  if [[ -n "${TOKEN}" ]]; then
    http_code=$(curl -sS -o /tmp/validate_out.json -w "%{http_code}" -X POST "${API_VALIDATE}" \
      -H 'Content-Type: application/json' \
      -H "Authorization: Bearer ${TOKEN}" \
      -d "{\"name\":\"${name}\",\"scope\":\"${scope}\",\"severity\":\"${severity}\",\"enabled\":${enabled},\"expression\":${expression_json}}" || true)
  else
    http_code=$(curl -sS -o /tmp/validate_out.json -w "%{http_code}" -X POST "${API_VALIDATE}" \
      -H 'Content-Type: application/json' \
      -d "{\"name\":\"${name}\",\"scope\":\"${scope}\",\"severity\":\"${severity}\",\"enabled\":${enabled},\"expression\":${expression_json}}" || true)
  fi
  if [[ "${http_code}" != "200" ]]; then
    if [[ "${http_code}" == "404" || "${http_code}" == "405" || -z "${http_code}" ]]; then
      log "Validation endpoint not available (HTTP ${http_code:-N/A}). Skipping validation."
      return 0
    fi
    log "Validation failed (HTTP ${http_code}). Response:";
    if [[ ${have_jq} -eq 1 ]]; then jq . /tmp/validate_out.json || true; else cat /tmp/validate_out.json || true; fi
    return 1
  fi
  log "Validation ok"
  return 0
}

create_rule() {
  local name="$1"; shift
  local scope="$1"; shift
  local severity="$1"; shift
  local expression_json="$1"; shift

  log "Create: name='${name}' scope='${scope}' severity='${severity}'"
  if ! validate_rule "${name}" "${scope}" "${severity}" "${expression_json}"; then
    log "Skip create due to validation error: ${name}"
    return 1
  fi
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "DRY-RUN create payload prepared."
    return 0
  fi
  local http_code
  local AUTH_ARGS=()
  if [[ -n "${TOKEN}" ]]; then AUTH_ARGS=( -H "Authorization: Bearer ${TOKEN}" ); fi
  if [[ -n "${TOKEN}" ]]; then
    http_code=$(curl -sS -o /tmp/create_out.json -w "%{http_code}" -X POST "${API_RULES}" \
      -H 'Content-Type: application/json' \
      -H "Authorization: Bearer ${TOKEN}" \
      -d "{\"name\":\"${name}\",\"scope\":\"${scope}\",\"severity\":\"${severity}\",\"enabled\":true,\"expression\":${expression_json}}" || true)
  else
    http_code=$(curl -sS -o /tmp/create_out.json -w "%{http_code}" -X POST "${API_RULES}" \
      -H 'Content-Type: application/json' \
      -d "{\"name\":\"${name}\",\"scope\":\"${scope}\",\"severity\":\"${severity}\",\"enabled\":true,\"expression\":${expression_json}}" || true)
  fi
  if [[ "${http_code}" != "200" && "${http_code}" != "201" ]]; then
    log "Create failed (HTTP ${http_code}). Response:";
    if [[ ${have_jq} -eq 1 ]]; then jq . /tmp/create_out.json || true; else cat /tmp/create_out.json || true; fi
    return 1
  fi
  if [[ ${have_jq} -eq 1 ]]; then jq . /tmp/create_out.json || true; else cat /tmp/create_out.json || true; fi
}

log "Seeding KYT rules to ${API_RULES} (validate=${API_VALIDATE})..."

# 1) Bridge Activity
create_rule "Bridge Activity (event_type=bridge)" "tx" "medium" '{"event_type":"bridge"}' || true

# 2) Cross-Chain Exposure (chains>=2 & hops<=3)
create_rule "Cross-Chain Exposure (chains>=2 & hops<=3)" "address" "high" '{"all":[{"chains_involved":{">=":2}},{"cross_chain_hops":{"<=":3}}]}' || true

# 3) Cross-Chain Exposure in time window
create_rule "Cross-Chain Exposure (chains>=2 & hops<=2 in window)" "address" "high" '{"all":[{"chains_involved":{">=":2}},{"cross_chain_hops":{"<=":2}},{"from_timestamp":{"==":"2024-01-01T00:00:00Z"}},{"to_timestamp":{"==":"2024-12-31T23:59:59Z"}}]}' || true

# 4) DEX Swap (einfach): event_type = dex_swap
create_rule "DEX Swap (event_type=dex_swap)" "tx" "medium" '{"event_type":"dex_swap"}' || true

echo "Done."
