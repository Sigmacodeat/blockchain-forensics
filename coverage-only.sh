#!/bin/bash
# Langsamer Coverage-Report (optional)

cd backend
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
cd ..
echo "Coverage Report: $?"
