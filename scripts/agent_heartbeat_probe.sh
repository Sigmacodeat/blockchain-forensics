#!/usr/bin/env bash
# Lightweight probe to trigger AI Agent heartbeat periodically
# Usage: ./scripts/agent_heartbeat_probe.sh [--count N] [--interval SECONDS]

set -euo pipefail
COUNT=1
INTERVAL=5

while [[ $# -gt 0 ]]; do
  case "$1" in
    --count)
      COUNT="$2"; shift 2;;
    --interval)
      INTERVAL="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

for i in $(seq 1 "$COUNT"); do
  curl -s -X POST http://localhost:8000/api/v1/agent/heartbeat >/dev/null || true
  if [[ "$i" -lt "$COUNT" ]]; then sleep "$INTERVAL"; fi
done
