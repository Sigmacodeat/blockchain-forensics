#!/bin/bash

# Quick Test Script - Verify all products are startable
# Usage: ./QUICK_TEST.sh

echo "🧪 Testing AppSumo Products..."
echo ""

PRODUCTS=(
  "chatbot-pro:3001:8001"
  "wallet-guardian:3002:8002"
  "analytics-pro:3003:8003"
)

for product_config in "${PRODUCTS[@]}"; do
  IFS=':' read -r product frontend_port backend_port <<< "$product_config"
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Testing: $product"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  # Check if directory exists
  if [ ! -d "$product" ]; then
    echo "❌ Directory not found: $product"
    continue
  fi
  
  cd "$product" || exit
  
  # Check required files
  echo "📁 Checking files..."
  
  files=(
    "docker-compose.yml"
    "frontend/package.json"
    "frontend/src/App.jsx"
    "frontend/src/pages/LandingPage.jsx"
    "frontend/src/pages/Dashboard.jsx"
    "backend/app/main.py"
    "backend/requirements.txt"
    "README.md"
  )
  
  all_files_exist=true
  for file in "${files[@]}"; do
    if [ -f "$file" ]; then
      echo "  ✅ $file"
    else
      echo "  ❌ $file (MISSING!)"
      all_files_exist=false
    fi
  done
  
  if [ "$all_files_exist" = false ]; then
    echo ""
    echo "⚠️  Some files are missing!"
    cd ..
    continue
  fi
  
  echo ""
  echo "🐳 Starting Docker containers..."
  
  # Start containers (detached)
  docker-compose up -d > /dev/null 2>&1
  
  # Wait for services to start
  echo "⏳ Waiting for services to start (10s)..."
  sleep 10
  
  # Test Backend Health
  echo ""
  echo "🔍 Testing Backend..."
  backend_response=$(curl -s "http://localhost:$backend_port/health" || echo "FAILED")
  
  if [[ "$backend_response" == *"healthy"* ]] || [[ "$backend_response" == *"running"* ]]; then
    echo "  ✅ Backend responding on port $backend_port"
  else
    echo "  ❌ Backend NOT responding on port $backend_port"
    echo "  Response: $backend_response"
  fi
  
  # Test Frontend
  echo ""
  echo "🔍 Testing Frontend..."
  frontend_response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$frontend_port" || echo "000")
  
  if [ "$frontend_response" = "200" ] || [ "$frontend_response" = "304" ]; then
    echo "  ✅ Frontend responding on port $frontend_port"
  else
    echo "  ❌ Frontend NOT responding on port $frontend_port (HTTP $frontend_response)"
  fi
  
  echo ""
  echo "🛑 Stopping containers..."
  docker-compose down > /dev/null 2>&1
  
  echo ""
  echo "✅ Test complete for $product"
  echo ""
  
  cd ..
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All tests complete!"
echo ""
echo "✨ Products tested: ${#PRODUCTS[@]}"
echo ""
echo "Next steps:"
echo "1. Review any errors above"
echo "2. Fix any missing files"
echo "3. Create screenshots"
echo "4. Record demo videos"
echo "5. Submit to AppSumo!"
echo ""
echo "🚀 Ready to launch!"
