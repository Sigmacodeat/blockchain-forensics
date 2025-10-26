#!/usr/bin/env bash
set -euo pipefail

note() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
ok() { echo -e "\033[1;32m[OK]\033[0m  $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[1;31m[ERR]\033[0m  $*"; }

wait_health() {
  local url="$1"; local name="$2"; local i=0
  note "Waiting for ${name} backend health at ${url}/health ..."
  until curl -fsS "${url}/health" >/dev/null 2>&1; do
    i=$((i+1))
    if [ $i -gt 60 ]; then err "${name} health check timeout"; exit 1; fi
    sleep 2
  done
  ok "${name} healthy"
}

main() {
  note "🚀 Testing Master Compose Environment - 6 Production-Ready Apps"
  note "📊 Apps: Wallet Guardian, Transaction Inspector, NFT Manager, Complete Security, DeFi Tracker, Analytics Pro"

  # Test Wallet Guardian (3002/8002)
  wait_health "http://localhost:8002" "Wallet Guardian"
  curl -fsS "http://localhost:8002/api/portfolio/0x742d35cc6634c0532925a3b844bc454e4438f44e" >/dev/null
  ok "Wallet Guardian portfolio OK"

  # Test Transaction Inspector (3004/8004)
  wait_health "http://localhost:8004" "Transaction Inspector"
  curl -fsS -X POST "http://localhost:8004/api/trace/tx" \
    -H 'Content-Type: application/json' \
    -d '{"tx_hash":"0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef","chain":"ethereum"}' >/dev/null
  ok "Transaction Inspector trace OK"

  # Test NFT Manager (3006/8006)
  wait_health "http://localhost:8006" "NFT Manager"
  curl -fsS "http://localhost:8006/api/portfolio" \
    -H 'Content-Type: application/json' \
    -d '{"address":"0x742d35cc6634c0532925a3b844bc454e4438f44e","chain":"ethereum"}' >/dev/null
  ok "NFT Manager portfolio OK"

  # Test Complete Security (3011/8011)
  wait_health "http://localhost:8011" "Complete Security"
  curl -fsS "http://localhost:8011/api/security/threats" >/dev/null
  ok "Complete Security threats OK"

  # Test DeFi Tracker (3007/8007)
  wait_health "http://localhost:8007" "DeFi Tracker"
  curl -fsS "http://localhost:8007/api/protocols" >/dev/null
  ok "DeFi Tracker protocols OK"

  # Test Analytics Pro (3004/8003) - ACHTUNG: Port-Konflikt! Frontend 3004, Backend 8003
  wait_health "http://localhost:8003" "Analytics Pro"
  curl -fsS "http://localhost:8003/api/portfolio/0x742d35cc6634c0532925a3b844bc454e4438f44e" >/dev/null
  ok "Analytics Pro portfolio OK"

  note "✅ ALL 6 APPS RUNNING SUCCESSFULLY IN MASTER COMPOSE!"
  note "🌐 Available Frontends:"
  note "   Wallet Guardian: http://localhost:3002"
  note "   Transaction Inspector: http://localhost:3004"
  note "   NFT Manager: http://localhost:3006"
  note "   Complete Security: http://localhost:3011"
  note "   DeFi Tracker: http://localhost:3007"
  note "   Analytics Pro: http://localhost:3004 (Frontend), Backend: http://localhost:8003"
  note ""
  note "🔧 Backends all healthy and responding to API calls!"
  note "🚀 Master Compose Test COMPLETED SUCCESSFULLY!"
}

main "$@"
