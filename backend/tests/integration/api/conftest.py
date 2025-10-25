# Ensure the backend 'app' package is importable
import os
import sys
from pathlib import Path

# Project root: /Users/msc/CascadeProjects/blockchain-forensics
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Test-friendly environment
os.environ.setdefault("DISABLE_LIFESPAN", "1")
os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
