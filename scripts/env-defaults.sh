#!/usr/bin/env bash
# Safe default environment for local dev (no real keys). Source with:  source scripts/env-defaults.sh
# Adjust values as needed. This does not touch .env automatically.

# --- Caching & Metrics ---
export ENABLE_SCAN_CACHE=1
export SCAN_CACHE_TTL=120
export ENABLE_METRICS=1

# --- Sanctions Sources (overrideable) ---
export OFAC_URL="https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/sdn.csv"
export UN_URL="https://scsanctions.un.org/resources/xml/en/consolidated.xml"
export UK_URL="https://sanctionslistservice.ofsi.hmtreasury.gov.uk/api/search/download?format=csv"
# export EU_URL="https://data.europa.eu/data/datasets/sanctionsmap"

# --- Optional Bridge Contracts & Topics for cross-chain log scan ---
# Fill with real contracts later; examples below are placeholders
export BRIDGE_CONTRACTS_JSON='{"ethereum":[], "polygon":[]}'
export BRIDGE_TOPICS_JSON='{}'

# --- Bridge Topic Map for lightweight log decoding ---
export BRIDGE_TOPIC_MAP_JSON='{
  "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":"Transfer",
  "0x98ea5fcaedb8f558b5756fa0fe58f3d82405463e99e36fcff7bcac28cf383e84":"SendToChain",
  "0x5fe5a0b2b1d5b6b6d9b2b71e1a92c9a1bde7b27fa8d7d8b6f9eb7a0f2c913b17":"LogMessagePublished",
  "0x0c7b68e2b1b99c8cf5f7e7d7f6845a5704c0e6f76fce0c2f3e6f9f2ad3c2b0a4":"FundsDeposited"
}'

# --- RPC URLs (leave empty now; set later for real testing) ---
# export ETHEREUM_RPC_URL=""
# export POLYGON_RPC_URL=""
# export ARBITRARY_BSC_RPC_URL=""
# export AVALANCHE_RPC_URL=""
# export ARBITRUM_RPC_URL=""
# export OPTIMISM_RPC_URL=""
# export BASE_RPC_URL=""
# export LINEA_RPC_URL=""
# export SCROLL_RPC_URL=""
# export ZKSYNC_RPC_URL=""
# export MANTLE_RPC_URL=""
# export BLAST_RPC_URL=""
# export SOLANA_RPC_URL=""

# --- Intelligence Feeds (set keys later) ---
# export CHAINABUSE_API_KEY=""
# export CRYPTOSCAMDB_API_KEY=""

# --- Neo4j (only enable when you want to write to DB) ---
# export TEST_MODE=0
# export NEO4J_URI="bolt://localhost:7687"
# export NEO4J_USER="neo4j"
# export NEO4J_PASSWORD=""

# Print a short summary
printf "Loaded default dev env (safe). Edit scripts/env-defaults.sh to customize.\n"
