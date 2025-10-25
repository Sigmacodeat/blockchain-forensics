#!/bin/bash
# Stop Script for Two-Tier Demo System
# ======================================

echo "🛑 Stopping Two-Tier Demo System..."
echo ""

# Load PIDs if available
if [ -f "/tmp/demo_system_pids.sh" ]; then
    source /tmp/demo_system_pids.sh
    
    echo "Stopping processes..."
    
    if [ -n "$BACKEND_PID" ]; then
        echo "  Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || echo "  Backend already stopped"
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        echo "  Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || echo "  Frontend already stopped"
    fi
    
    if [ -n "$CLEANUP_PID" ]; then
        echo "  Stopping Cleanup Service (PID: $CLEANUP_PID)..."
        kill $CLEANUP_PID 2>/dev/null || echo "  Cleanup already stopped"
    fi
    
    rm /tmp/demo_system_pids.sh
else
    echo "⚠️  PID file not found. Trying to find processes..."
    
    # Try to find and kill uvicorn
    pkill -f "uvicorn app.main:app" && echo "  Stopped Backend" || true
    
    # Try to find and kill vite
    pkill -f "vite" && echo "  Stopped Frontend" || true
    
    # Try to find and kill cleanup
    pkill -f "demo_cleanup.py" && echo "  Stopped Cleanup" || true
fi

echo ""
echo "Stopping Docker containers..."
docker-compose down

echo ""
echo "✅ All services stopped!"
echo ""
echo "💡 To start again: ./scripts/start-demo-system.sh"
