#!/usr/bin/env bash
set -euo pipefail

# Generates TypeScript and Python SDKs from backend/docs/openapi.yaml into docs/sdk/
# Requires Docker with openapitools/openapi-generator-cli image

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENAPI_FILE="$ROOT_DIR/backend/docs/openapi.yaml"
OUT_TS="$ROOT_DIR/docs/sdk/typescript"
OUT_PY="$ROOT_DIR/docs/sdk/python"

mkdir -p "$OUT_TS" "$OUT_PY"

echo "Generating TypeScript SDK to $OUT_TS ..."
docker run --rm -v "$ROOT_DIR":/local openapitools/openapi-generator-cli generate \
  -i /local/backend/docs/openapi.yaml \
  -g typescript-fetch \
  -o /local/docs/sdk/typescript \
  --additional-properties=supportsES6=true,typescriptThreePlus=true \
  --skip-validate-spec

echo "Generating Python SDK to $OUT_PY ..."
docker run --rm -v "$ROOT_DIR":/local openapitools/openapi-generator-cli generate \
  -i /local/backend/docs/openapi.yaml \
  -g python \
  -o /local/docs/sdk/python \
  --additional-properties=packageName=blockchain_forensics_sdk \
  --skip-validate-spec

echo "Done. SDKs generated under docs/sdk/."

# --- Scaffolding: TypeScript package.json & README (if missing) ---
if [ ! -f "$OUT_TS/package.json" ]; then
  cat > "$OUT_TS/package.json" <<'PKG'
{
  "name": "@sigmacode/blockchain-forensics-sdk",
  "version": "0.1.0",
  "description": "TypeScript SDK for Blockchain Forensics API (generated from OpenAPI)",
  "license": "MIT",
  "type": "module",
  "sideEffects": false,
  "main": "index.ts",
  "types": "index.ts",
  "publishConfig": {
    "access": "public"
  }
}
PKG
fi

if [ ! -f "$OUT_TS/README.md" ]; then
  cat > "$OUT_TS/README.md" <<'README'
# Blockchain Forensics TypeScript SDK

Generated via OpenAPI Generator (typescript-fetch).

Install (local path):
```
npm install ./docs/sdk/typescript
```

Usage:
```
import { Configuration, DefaultApi } from "@sigmacode/blockchain-forensics-sdk"
const api = new DefaultApi(new Configuration({ basePath: "http://localhost:8000/api/v1" }))
```
README
fi

# --- Scaffolding: Python pyproject & README (if missing) ---
if [ ! -f "$OUT_PY/pyproject.toml" ]; then
  cat > "$OUT_PY/pyproject.toml" <<'PYPROJ'
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "blockchain_forensics_sdk"
version = "0.1.0"
description = "Python SDK for Blockchain Forensics API (generated from OpenAPI)"
requires-python = ">=3.8"
license = { text = "MIT" }
readme = "README.md"
dependencies = []
PYPROJ
fi

if [ ! -f "$OUT_PY/README.md" ]; then
  cat > "$OUT_PY/README.md" <<'PREADME'
# Blockchain Forensics Python SDK

Generated via OpenAPI Generator (python).

Install (editable):
```
pip install -e ./docs/sdk/python
```

Usage:
```
from blockchain_forensics_sdk import ApiClient, Configuration, DefaultApi
cfg = Configuration(); cfg.host = 'http://localhost:8000/api/v1'
with ApiClient(cfg) as c:
    api = DefaultApi(c)
    print(api.api_v1_system_health_get())
```
PREADME
fi
