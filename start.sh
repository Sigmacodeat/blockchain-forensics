#!/bin/bash

# Blockchain Forensics Platform - Quickstart Script
# Startet alle Services in der richtigen Reihenfolge

set -e

echo "🚀 Starting Blockchain Forensics Platform..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please edit with your API keys!"
    echo "   - ETHEREUM_RPC_URL (Infura/Alchemy)"
    echo "   - OPENAI_API_KEY"
    echo "   - JWT_SECRET"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Start infrastructure
echo "📦 Starting infrastructure (Kafka, Neo4j, Postgres, Redis, Qdrant)..."
docker-compose up -d

echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30

# Check if services are running
echo "🔍 Checking service health..."
docker-compose ps

# Start Backend
echo ""
echo "🐍 Starting Backend API..."
cd backend

if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "✅ Backend ready. Starting on port 8000..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Start Frontend
echo ""
echo "⚛️  Starting Frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

echo "✅ Frontend ready. Starting on port 3000..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Blockchain Forensics Platform is running!"
echo ""
echo "📍 Access Points:"
echo "   Frontend:     http://localhost:3000"
echo "   Backend API:  http://localhost:8000/docs"
echo "   Neo4j:        http://localhost:7474 (neo4j/forensics_password_change_me)"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; docker-compose down; echo '✅ Stopped'; exit 0" INT

wait
