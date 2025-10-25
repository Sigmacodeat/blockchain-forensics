#!/bin/bash
set -euo pipefail
echo "🚀 Deploying Backend to Render via Blueprint..."
echo "1. Go to https://dashboard.render.com/"
echo "2. Click 'New' → 'Blueprint'"
echo "3. Connect GitHub repo: Sigmacodeat/blockchain-forensics"
echo "4. Copy ENV vars from .render-env file below:"
echo ""
cat .render-env
echo ""
echo "5. Click 'Apply' → Deploy will start automatically"
echo "6. Note the service URL (e.g. https://blockchain-forensics-backend.onrender.com)"
