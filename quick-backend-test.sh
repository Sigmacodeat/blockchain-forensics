#!/bin/bash
# Schnelle Backend-Tests ohne Coverage

cd backend
python -m pytest tests/ -v --tb=short -x --maxfail=5
cd ..
echo "Backend Tests: $?"
