#!/bin/bash

# Cache Management Script

echo "Blockchain Forensics Cache Manager"
echo "=================================="

# Check if Redis is running
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis CLI found"
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"

        # Show cache statistics
        echo ""
        echo "Cache Statistics:"
        redis-cli info keyspace | grep -E "(db0|keys|expires)"

        echo ""
        echo "Sample Cache Keys:"
        redis-cli keys "chat_response:*" | head -5
        redis-cli keys "ocr_result:*" | head -5
        redis-cli keys "kb_search:*" | head -5

    else
        echo "❌ Redis is not running"
        echo "Start Redis: sudo systemctl start redis-server (Linux) or brew services start redis (macOS)"
    fi
else
    echo "❌ Redis CLI not found. Install Redis first."
fi

echo ""
echo "To clear all cache:"
echo "redis-cli FLUSHALL"
echo ""
echo "To check cache hit rate:"
echo "redis-cli INFO stats | grep -E '(keyspace_hits|keyspace_misses)'"
echo ""
echo "For more information, see CACHE_SETUP.md"
