#!/bin/bash
set -euo pipefail
echo "🔍 Running Post-Deploy Smoke Tests..."
echo "Replace YOUR_BACKEND_URL and YOUR_FRONTEND_URL below:"
BACKEND_URL="https://YOUR_RENDER_BACKEND_URL.onrender.com"
FRONTEND_URL="https://YOUR_NETLIFY_FRONTEND_URL.netlify.app"

echo "1. Backend Health Check:"
curl -f "${BACKEND_URL}/health" || echo "❌ Backend health failed"

echo "2. Frontend Load Test:"
curl -f "${FRONTEND_URL}/" || echo "❌ Frontend load failed"

echo "3. CORS Test (API call from frontend):"
curl -f "${BACKEND_URL}/api/v1/ping" -H "Origin: ${FRONTEND_URL}" || echo "❌ CORS failed"

echo "4. OAuth Callback Test (should redirect):"
curl -L "${BACKEND_URL}/api/v1/auth/oauth/google/callback?code=test" || echo "❌ OAuth callback failed"

echo "✅ Smoke tests complete! Check outputs above."
