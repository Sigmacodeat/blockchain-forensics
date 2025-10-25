#!/usr/bin/env bash
set -euo pipefail
cat <<'ENV' > frontend/.netlify-env
VITE_API_URL=
VITE_GOOGLE_CLIENT_ID=
ENV
