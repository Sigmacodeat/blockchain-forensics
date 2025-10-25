#!/bin/bash
echo "🚀 Starting Blockchain Forensics Platform..."

# 1. Docker prüfen/starten
if ! docker info > /dev/null 2>&1; then
    echo "⏳ Starting Docker Desktop..."
    open -a Docker
    echo "   Waiting for Docker to start (20 seconds)..."
    sleep 20
fi

# 2. Database starten
echo "🐘 Starting PostgreSQL & Redis..."
cd /Users/msc/CascadeProjects/blockchain-forensics
docker-compose up -d postgres redis
echo "   Waiting for database to be ready (5 seconds)..."
sleep 5

# 3. Admin-Account erstellen
echo "👤 Creating admin account..."
cd backend
python create_admin.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Start Backend:"
echo "   cd backend && python -m uvicorn app.main:app --reload --port 8000"
echo ""
echo "2. Start Frontend (in new terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo "3. Login:"
echo "   URL:      http://localhost:3000/login"
echo "   Email:    admin@blockchain-forensics.com"
echo "   Password: Admin2025!Secure"
echo ""
