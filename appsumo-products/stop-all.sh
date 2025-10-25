#!/bin/bash

echo "🛑 STOPPING ALL 12 APPSUMO PRODUCTS"
echo "===================================="
echo ""

PRODUCTS=(
    "chatbot-pro"
    "wallet-guardian"
    "analytics-pro"
    "transaction-inspector"
    "dashboard-commander"
    "nft-manager"
    "defi-tracker"
    "tax-reporter"
    "agency-reseller"
    "power-suite"
    "complete-security"
    "trader-pack"
)

for product in "${PRODUCTS[@]}"; do
    echo "Stopping $product..."
    cd "$product"
    docker-compose down 2>/dev/null
    cd ..
done

echo ""
echo "✅ ALL PRODUCTS STOPPED!"
