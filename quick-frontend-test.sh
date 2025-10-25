#!/bin/bash
# Schnelle Frontend-Tests

cd frontend
npm run test -- --run --maxWorkers=2
cd ..
echo "Frontend Tests: $?"
