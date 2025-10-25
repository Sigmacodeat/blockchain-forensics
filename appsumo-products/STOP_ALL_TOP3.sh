#!/bin/bash
# Stop All Top 3 Products

echo "🛑 Stopping All Products..."
echo ""

# Function to stop a product
stop_product() {
    local name=$1
    local folder=$2
    
    if [ -f "/tmp/$folder-backend.pid" ]; then
        kill $(cat /tmp/$folder-backend.pid) 2>/dev/null
        rm /tmp/$folder-backend.pid
        echo "✅ $name backend stopped"
    fi
    
    if [ -f "/tmp/$folder-frontend.pid" ]; then
        kill $(cat /tmp/$folder-frontend.pid) 2>/dev/null
        rm /tmp/$folder-frontend.pid
        echo "✅ $name frontend stopped"
    fi
}

stop_product "ChatBot Pro" "chatbot-pro"
stop_product "Wallet Guardian" "wallet-guardian"
stop_product "Analytics Pro" "analytics-pro"

echo ""
echo "🎉 All products stopped!"
