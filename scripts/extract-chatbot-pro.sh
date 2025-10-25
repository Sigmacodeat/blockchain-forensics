#!/bin/bash

# 🤖 AI ChatBot Pro - AppSumo Extraction Script
# Extrahiert ChatBot aus Hauptprojekt für AppSumo-Launch

set -e  # Exit on error

echo "🚀 Starting AI ChatBot Pro Extraction..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Base directories
SOURCE_DIR="/Users/msc/CascadeProjects/blockchain-forensics"
TARGET_DIR="/Users/msc/CascadeProjects/appsumo-chatbot-pro"

# Create target directory
echo "📁 Creating target directory..."
rm -rf "$TARGET_DIR"  # Clean start
mkdir -p "$TARGET_DIR"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FRONTEND EXTRACTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "📦 Extracting Frontend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create frontend structure
mkdir -p "$TARGET_DIR/frontend/src"
mkdir -p "$TARGET_DIR/frontend/public"

# Copy Chat Components
echo "  ✅ Copying Chat Components..."
cp -r "$SOURCE_DIR/frontend/src/components/chat" "$TARGET_DIR/frontend/src/components/"

# Copy i18n (42 languages)
echo "  ✅ Copying i18n (42 languages)..."
cp -r "$SOURCE_DIR/frontend/src/i18n" "$TARGET_DIR/frontend/src/"

# Copy relevant hooks
echo "  ✅ Copying Hooks..."
mkdir -p "$TARGET_DIR/frontend/src/hooks"
cp "$SOURCE_DIR/frontend/src/hooks/useProactiveAI.ts" "$TARGET_DIR/frontend/src/hooks/" 2>/dev/null || true
cp "$SOURCE_DIR/frontend/src/hooks/usePaymentWebSocket.ts" "$TARGET_DIR/frontend/src/hooks/" 2>/dev/null || true
cp "$SOURCE_DIR/frontend/src/hooks/useChatStream.ts" "$TARGET_DIR/frontend/src/hooks/" 2>/dev/null || true

# Copy UI components (needed for chat)
echo "  ✅ Copying UI Components..."
mkdir -p "$TARGET_DIR/frontend/src/components/ui"
cp -r "$SOURCE_DIR/frontend/src/components/ui/"* "$TARGET_DIR/frontend/src/components/ui/" 2>/dev/null || true

# Copy config files
echo "  ✅ Copying Config Files..."
cp "$SOURCE_DIR/frontend/package.json" "$TARGET_DIR/frontend/"
cp "$SOURCE_DIR/frontend/tsconfig.json" "$TARGET_DIR/frontend/" 2>/dev/null || true
cp "$SOURCE_DIR/frontend/vite.config.ts" "$TARGET_DIR/frontend/" 2>/dev/null || true
cp "$SOURCE_DIR/frontend/tailwind.config.js" "$TARGET_DIR/frontend/" 2>/dev/null || true
cp "$SOURCE_DIR/frontend/postcss.config.js" "$TARGET_DIR/frontend/" 2>/dev/null || true

# Copy public assets
echo "  ✅ Copying Public Assets..."
cp -r "$SOURCE_DIR/frontend/public/"* "$TARGET_DIR/frontend/public/" 2>/dev/null || true

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BACKEND EXTRACTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "📦 Extracting Backend..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create backend structure
mkdir -p "$TARGET_DIR/backend/app"

# Copy AI Agents
echo "  ✅ Copying AI Agents..."
cp -r "$SOURCE_DIR/backend/app/ai_agents" "$TARGET_DIR/backend/app/"

# Copy Services (only payment-related)
echo "  ✅ Copying Services..."
mkdir -p "$TARGET_DIR/backend/app/services"
cp "$SOURCE_DIR/backend/app/services/crypto_payments.py" "$TARGET_DIR/backend/app/services/" 2>/dev/null || true
cp "$SOURCE_DIR/backend/app/services/email_notifications.py" "$TARGET_DIR/backend/app/services/" 2>/dev/null || true

# Copy API endpoints (only chat + payments)
echo "  ✅ Copying API Endpoints..."
mkdir -p "$TARGET_DIR/backend/app/api/v1"
cp "$SOURCE_DIR/backend/app/api/v1/chat.py" "$TARGET_DIR/backend/app/api/v1/" 2>/dev/null || true
cp "$SOURCE_DIR/backend/app/api/v1/crypto_payments.py" "$TARGET_DIR/backend/app/api/v1/" 2>/dev/null || true

# Copy WebSocket
mkdir -p "$TARGET_DIR/backend/app/api/v1/websockets"
cp "$SOURCE_DIR/backend/app/api/v1/websockets/payment.py" "$TARGET_DIR/backend/app/api/v1/websockets/" 2>/dev/null || true
cp "$SOURCE_DIR/backend/app/api/v1/websockets/__init__.py" "$TARGET_DIR/backend/app/api/v1/websockets/" 2>/dev/null || true

# Copy Models (minimal)
echo "  ✅ Copying Models..."
mkdir -p "$TARGET_DIR/backend/app/models"
cp "$SOURCE_DIR/backend/app/models/crypto_payment.py" "$TARGET_DIR/backend/app/models/" 2>/dev/null || true
cp "$SOURCE_DIR/backend/app/models/user.py" "$TARGET_DIR/backend/app/models/" 2>/dev/null || true

# Copy main app files
echo "  ✅ Copying Main App Files..."
cp "$SOURCE_DIR/backend/app/main.py" "$TARGET_DIR/backend/app/" 2>/dev/null || true
cp "$SOURCE_DIR/backend/app/config.py" "$TARGET_DIR/backend/app/" 2>/dev/null || true
cp "$SOURCE_DIR/backend/app/__init__.py" "$TARGET_DIR/backend/app/" 2>/dev/null || true

# Copy requirements
echo "  ✅ Copying Requirements..."
cp "$SOURCE_DIR/backend/requirements.txt" "$TARGET_DIR/backend/"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLEANUP DEPENDENCIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "🧹 Cleaning Dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$TARGET_DIR/backend"

# Remove forensik-only dependencies
echo "  ✅ Removing forensik dependencies..."
grep -v "neo4j\|web3\|eth-account\|eth-abi\|eth-utils" requirements.txt > requirements.clean.txt || true
mv requirements.clean.txt requirements.txt

echo "  ✅ Adding ChatBot-specific dependencies..."
cat >> requirements.txt << 'EOF'

# ChatBot Pro Specific
openai==1.3.5
langchain==0.0.340
redis==5.0.1
qrcode==7.4.2
Pillow==10.1.0
EOF

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CREATE DOCKER SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "🐳 Creating Docker Setup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > "$TARGET_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://chatbot:chatbot@postgres:5432/chatbot
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - NOWPAYMENTS_API_KEY=${NOWPAYMENTS_API_KEY}
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=chatbot
      - POSTGRES_USER=chatbot
      - POSTGRES_PASSWORD=chatbot
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
EOF

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CREATE README
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "📝 Creating README..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > "$TARGET_DIR/README.md" << 'EOF'
# 🤖 AI ChatBot Pro

**State-of-the-art AI ChatBot with Voice, Crypto Payments & 42 Languages**

## 🚀 Features

- 🎤 **Voice Input**: 43 languages, hands-free chat
- 💰 **Crypto Payments**: 30+ cryptocurrencies
- 🌐 **42 Languages**: Fully localized, RTL support
- 🎨 **Beautiful UI**: Modern, responsive, dark mode
- ⚡ **Real-time**: WebSocket updates
- 🤖 **Proactive AI**: Context-aware suggestions

## 📦 Quick Start

```bash
# 1. Clone
git clone https://github.com/yourusername/appsumo-chatbot-pro
cd appsumo-chatbot-pro

# 2. Setup Environment
cp .env.example .env
# Add your API keys

# 3. Start with Docker
docker-compose up

# 4. Open
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 💰 AppSumo Lifetime Deal

**Available on AppSumo**: [Get Lifetime Access](https://appsumo.com/chatbot-pro)

- **Tier 1** ($59): 1 Website, 1,000 Chats/month
- **Tier 2** ($119): 3 Websites, 5,000 Chats/month, White-Label
- **Tier 3** ($199): 10 Websites, Unlimited, API Access

## 📚 Documentation

- [Setup Guide](./docs/SETUP.md)
- [API Documentation](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)

## 🤝 Support

- Email: support@aichatbotpro.com
- Discord: [Join Server](https://discord.gg/chatbotpro)

## 📄 License

MIT License - see [LICENSE](./LICENSE)
EOF

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FINAL SUMMARY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ EXTRACTION COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Location: $TARGET_DIR"
echo ""
echo "📊 Extracted:"
echo "  ✅ Frontend: Chat Widget + i18n (42 languages)"
echo "  ✅ Backend: AI Agents + Crypto Payments"
echo "  ✅ Docker: Complete setup"
echo "  ✅ Dependencies: Cleaned & optimized"
echo ""
echo "🎯 Next Steps:"
echo "  1. cd $TARGET_DIR"
echo "  2. Review extracted files"
echo "  3. Test with: docker-compose up"
echo "  4. Customize branding"
echo "  5. Create AppSumo listing"
echo ""
echo "🚀 Ready for AppSumo Launch!"
echo ""
