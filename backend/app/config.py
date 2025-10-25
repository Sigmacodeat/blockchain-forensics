"""Configuration Management"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional


class Settings(BaseSettings):
    """Application Settings"""
    
    # Application
    APP_NAME: str = "Blockchain Forensics Platform"
    VERSION: str = Field("0.1.0", json_schema_extra={"env": "VERSION"})
    DEBUG: bool = False
    
    # Blockchain RPC
    ETHEREUM_RPC_URL: str = "https://mainnet.infura.io/v3/demo"
    ETHEREUM_WS_URL: str = ""
    ETHEREUM_ARCHIVE_NODE: str = ""
    
    # L2 RPC URLs
    POLYGON_RPC_URL: str = "mock"
    ARBITRUM_RPC_URL: str = "mock"
    OPTIMISM_RPC_URL: str = "mock"
    BASE_RPC_URL: str = "mock"
    
    SOLANA_RPC_URL: str = ""
    BITCOIN_RPC_URL: str = ""
    BITCOIN_RPC_USER: str = ""
    BITCOIN_RPC_PASSWORD: str = ""
    
    # Databases
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    POSTGRES_URL: str = "postgresql://forensics:forensics_pass@localhost:5435/blockchain_forensics"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SCHEMA_REGISTRY_URL: str = ""
    KAFKA_DLQ_TOPIC: str = "dlq.events"
    
    # AI Services
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    KILO_API_KEY: Optional[str] = Field(None, json_schema_extra={"env": "KILO_API_KEY"})
    KILO_BASE_URL: Optional[str] = Field(None, json_schema_extra={"env": "KILO_BASE_URL"})
    GROK_CODEFAST_API_KEY: Optional[str] = Field(None, json_schema_extra={"env": "GROK_CODEFAST_API_KEY"})
    GROK_CODEFAST_BASE_URL: Optional[str] = Field(None, json_schema_extra={"env": "GROK_CODEFAST_BASE_URL"})
    
    # ML Models
    ML_MODEL_PATH: str = "/app/models"
    XGBOOST_MODEL_PATH: str = "/app/models/risk_classifier.json"
    
    # External APIs
    ETHERSCAN_API_KEY: str = ""
    OFAC_SANCTIONS_URL: str = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADVANCED.CSV"
    
    # Crypto Payments (NOWPayments)
    NOWPAYMENTS_API_KEY: str = Field("", json_schema_extra={"env": "NOWPAYMENTS_API_KEY"})
    NOWPAYMENTS_IPN_SECRET: str = Field("", json_schema_extra={"env": "NOWPAYMENTS_IPN_SECRET"})
    NOWPAYMENTS_SANDBOX: bool = Field(True, json_schema_extra={"env": "NOWPAYMENTS_SANDBOX"})
    BACKEND_URL: str = Field("http://localhost:8000", json_schema_extra={"env": "BACKEND_URL"})
    FRONTEND_URL: str = Field("http://localhost:5173", json_schema_extra={"env": "FRONTEND_URL"})
    
    # Email Configuration
    EMAIL_ENABLED: bool = Field(False, json_schema_extra={"env": "EMAIL_ENABLED"})
    EMAIL_BACKEND: str = Field("smtp", json_schema_extra={"env": "EMAIL_BACKEND"})  # smtp, sendgrid
    EMAIL_FROM: str = Field("noreply@blockchain-forensics.com", json_schema_extra={"env": "EMAIL_FROM"})
    SUPPORT_EMAIL: str = Field("support@blockchain-forensics.com", json_schema_extra={"env": "SUPPORT_EMAIL"})
    
    # SMTP Configuration
    SMTP_HOST: str = Field("smtp.gmail.com", json_schema_extra={"env": "SMTP_HOST"})
    SMTP_PORT: int = Field(587, json_schema_extra={"env": "SMTP_PORT"})
    SMTP_USER: Optional[str] = Field(None, json_schema_extra={"env": "SMTP_USER"})
    SMTP_PASSWORD: Optional[str] = Field(None, json_schema_extra={"env": "SMTP_PASSWORD"})
    SMTP_USE_TLS: bool = Field(True, json_schema_extra={"env": "SMTP_USE_TLS"})
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = Field(None, json_schema_extra={"env": "SENDGRID_API_KEY"})
    
    # Security
    SECRET_KEY: str = Field("test-secret", json_schema_extra={"env": "SECRET_KEY"})  # Main secret key for JWT and other crypto
    JWT_SECRET: str = ""  # Deprecated, use SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    FORCE_HTTPS_REDIRECT: bool = Field(False, json_schema_extra={"env": "FORCE_HTTPS_REDIRECT"})
    TRUSTED_HOSTS: List[str] = ["*"]

    # OAuth (Google)
    GOOGLE_CLIENT_ID: Optional[str] = Field(None, json_schema_extra={"env": "GOOGLE_CLIENT_ID"})
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None, json_schema_extra={"env": "GOOGLE_CLIENT_SECRET"})
    # Optional: override callback base if running behind proxy; otherwise derived from request
    OAUTH_CALLBACK_PATH: str = Field("/api/v1/auth/oauth/google/callback", json_schema_extra={"env": "OAUTH_CALLBACK_PATH"})
    # Admin allowlist: comma-separated or JSON-like list of emails
    ADMIN_EMAILS: list[str] = Field(default_factory=list, json_schema_extra={"env": "ADMIN_EMAILS"})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Fallback: if JWT_SECRET is set but not SECRET_KEY
        if self.JWT_SECRET and not kwargs.get('SECRET_KEY'):
            self.SECRET_KEY = self.JWT_SECRET

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _coerce_cors_origins(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
                return [p for p in parts if p]
            return [p.strip() for p in s.split(",") if p.strip()]
        return v

    @field_validator("DEX_ROUTERS_EVM", mode="before")
    @classmethod
    def _coerce_dex_routers(cls, v):
        # Accept list or comma-separated string, normalize to lowercase
        if v is None:
            return []
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
            else:
                parts = [p.strip() for p in s.split(",") if p.strip()]
            return [p.lower() for p in parts]
        if isinstance(v, (list, tuple)):
            return [str(p).lower() for p in v]
        return []

    @field_validator("CORS_ALLOW_METHODS", mode="before")
    @classmethod
    def _coerce_cors_methods(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
                return [p.upper() for p in parts if p]
            return [p.strip().upper() for p in s.split(",") if p.strip()]
        return v

    @field_validator("CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def _coerce_cors_headers(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
                return [p for p in parts if p]
            return [p.strip() for p in s.split(",") if p.strip()]
        return v

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def _coerce_trusted_hosts(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
                return [p for p in parts if p]
            return [p.strip() for p in s.split(",") if p.strip()]
        return v
        return []

    @field_validator("IDEMPOTENCY_ALLOWLIST", mode="before")
    @classmethod
    def _coerce_idem_allow(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
                return [p for p in parts if p]
            return [p.strip() for p in s.split(",") if p.strip()]
        if isinstance(v, (list, tuple)):
            return [str(p).strip() for p in v if str(p).strip()]
        return []

    @field_validator("IDEMPOTENCY_BLOCKLIST", mode="before")
    @classmethod
    def _coerce_idem_block(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
                return [p for p in parts if p]
            return [p.strip() for p in s.split(",") if p.strip()]
        if isinstance(v, (list, tuple)):
            return [str(p).strip() for p in v if str(p).strip()]
        return []

    @field_validator("IDEMPOTENCY_METHODS", mode="before")
    @classmethod
    def _coerce_idem_methods(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
                return [p.upper() for p in parts if p]
            return [p.strip().upper() for p in s.split(",") if p.strip()]
        if isinstance(v, (list, tuple)):
            return [str(p).upper().strip() for p in v if str(p).strip()]
        return ["POST", "PUT", "PATCH", "DELETE"]

    @field_validator("ADMIN_EMAILS", mode="before")
    @classmethod
    def _coerce_admin_emails(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith("[") and s.endswith("]"):
                s2 = s[1:-1]
                parts = [p.strip().strip('"').strip("'") for p in s2.split(",") if p.strip()]
            else:
                parts = [p.strip() for p in s.split(",") if p.strip()]
            # normalize emails to lowercase
            return [p.lower() for p in parts]
        if isinstance(v, (list, tuple)):
            return [str(p).lower().strip() for p in v if str(p).strip()]
        return []
    
    # Service Ports
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    
    # Tracing Config
    MAX_TRACE_DEPTH: int = 10
    MAX_NODES_PER_TRACE: int = 10000
    TAINT_MODEL: str = "proportional"  # fifo, proportional, haircut
    MIN_TAINT_THRESHOLD: float = 0.01
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field("http://localhost:4318", json_schema_extra={"env": "OTEL_EXPORTER_OTLP_ENDPOINT"})
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    JSON_LOGS: bool = Field(False, json_schema_extra={"env": "JSON_LOGS"})
    LOG_FILE: Optional[str] = Field(None, json_schema_extra={"env": "LOG_FILE"})
    SENTRY_DSN: str = ""
    METRICS_ENABLED: bool = Field(True, json_schema_extra={"env": "METRICS_ENABLED"})
    ENVIRONMENT: str = Field("development", json_schema_extra={"env": "ENVIRONMENT"})
    
    # Feature Flags
    ENABLE_ML_CLUSTERING: bool = True
    ENABLE_CROSS_CHAIN: bool = False
    ENABLE_AI_AGENTS: bool = True
    ENABLE_AGENT_TOOL_RBAC: bool = False
    ENABLE_KAFKA_STREAMING: bool = Field(False, json_schema_extra={"env": "ENABLE_KAFKA_STREAMING"})

    # Alert Engine Configuration (erweitert)
    ALERT_DEDUP_ENABLED: bool = Field(True, json_schema_extra={"env": "ALERT_DEDUP_ENABLED"})
    ALERT_DEDUP_WINDOW_SECONDS: int = Field(300, json_schema_extra={"env": "ALERT_DEDUP_WINDOW_SECONDS"})  # 5 minutes

    # Neue Alert Engine Settings
    ALERT_BATCH_SIZE: int = Field(100, json_schema_extra={"env": "ALERT_BATCH_SIZE"})
    ALERT_PROCESSING_INTERVAL_SECONDS: int = Field(30, json_schema_extra={"env": "ALERT_PROCESSING_INTERVAL_SECONDS"})
    ALERT_MAX_RULES_PER_ENTITY: int = Field(10, json_schema_extra={"env": "ALERT_MAX_RULES_PER_ENTITY"})
    ALERT_ENABLE_NOTIFICATIONS: bool = Field(True, json_schema_extra={"env": "ALERT_ENABLE_NOTIFICATIONS"})
    ALERT_NOTIFICATION_WEBHOOK_URL: Optional[str] = Field(None, json_schema_extra={"env": "ALERT_NOTIFICATION_WEBHOOK_URL"})

    # Auto-Investigate
    AUTO_INVESTIGATE_HIGH_RISK_THRESHOLD: float = Field(0.7, json_schema_extra={"env": "AUTO_INVESTIGATE_HIGH_RISK_THRESHOLD"})

    # Compliance - Fuzzy Screening
    FUZZY_NAME_THRESHOLD: float = Field(0.85, json_schema_extra={"env": "FUZZY_NAME_THRESHOLD"})
    FUZZY_MAX_MATCHES: int = Field(10, json_schema_extra={"env": "FUZZY_MAX_MATCHES"})

    # Bridge Detection Config (Ethereum)
    # Comma-separated list of known bridge contract addresses (lowercase or checksummed)
    BRIDGE_CONTRACTS_ETH: str = ""
    # Optional list of method selectors (e.g., ["0xa9059cbb"]) to identify bridge calls
    BRIDGE_METHOD_SELECTORS: list[str] = []
    # Optional mapping: topic0 hex (lowercase) → destination chain hint
    # Diese Hints werden von Bridge-Detection genutzt, wenn mehrere Gegenketten möglich sind.
    BRIDGE_TOPICS_CHAIN_HINTS: dict[str, str] = Field(
        default_factory=lambda: {
            # Wormhole LogMessagePublished (je nach Kontext kann dies variieren)
            "0x6eb224fb001ed210e379b335e35efe88672a8ce935d981a6896b27ffdf52a3b2": "solana",
            # Arbitrum L1 -> L2 MessageDelivered
            "0x23be8e12e420b5da9fb98d8102572f640fb3c11a0085060472dfc0ed194b3cf7": "arbitrum",
            # Optimism ERC20DepositInitiated
            "0x73d170910aba9e6d50b102db522b1dbcd796216f5128b445aa2135272886497e": "optimism",
            # Polygon PoS LockedERC20 (häufiger Indikator Richtung polygon)
            "0x103fed9db65eac19c4d870f49ab7520fe03b99f1838e5996caf47e9e43308392": "polygon",
            # Uniswap V2 Sync/Swap sind KEINE Bridges, nur als Beispiel NICHT mappen
            # LayerZero/Stargate spezifische Topics können projektspezifisch ergänzt werden
        },
        json_schema_extra={"env": "BRIDGE_TOPICS_CHAIN_HINTS"},
    )

    # DEX Routers (EVM)
    # List of router contract addresses used to heuristically detect swaps
    DEX_ROUTERS_EVM: list[str] = Field(default_factory=list, json_schema_extra={"env": "DEX_ROUTERS_EVM"})
    
    # Bridge Detection Config (L2s)
    BRIDGE_CONTRACTS_POLYGON: str = ""
    BRIDGE_CONTRACTS_ARBITRUM: str = ""
    BRIDGE_CONTRACTS_OPTIMISM: str = ""
    BRIDGE_CONTRACTS_BASE: str = ""
    
    # Bridge Detection Config (Solana)
    # List of known program IDs that indicate bridging
    BRIDGE_PROGRAMS_SOL: list[str] = []

    # Solana RPC Robustness
    SOL_RPC_TIMEOUT_SECS: int = 20
    SOL_RPC_MAX_RETRIES: int = 5
    SOL_RPC_BASE_DELAY_MS: int = 250
    SOL_RPC_MAX_DELAY_MS: int = 5000

    IDEMPOTENCY_TTL_SECONDS: int = Field(60, json_schema_extra={"env": "IDEMPOTENCY_TTL_SECONDS"})
    IDEMPOTENCY_ALLOWLIST: list[str] = Field(default_factory=list, json_schema_extra={"env": "IDEMPOTENCY_ALLOWLIST"})
    IDEMPOTENCY_BLOCKLIST: list[str] = Field(default_factory=list, json_schema_extra={"env": "IDEMPOTENCY_BLOCKLIST"})
    IDEMPOTENCY_METHODS: list[str] = Field(default_factory=lambda: ["POST", "PUT", "PATCH", "DELETE"], json_schema_extra={"env": "IDEMPOTENCY_METHODS"})
    
    # Pydantic v2 settings config
    # Allow disabling .env loading via IGNORE_DOTENV=1 (useful in containers)
    _use_env_file = not (
        os.getenv("TEST_MODE") == "1" or os.getenv("PYTEST_CURRENT_TEST") or os.getenv("IGNORE_DOTENV") == "1"
    )
    model_config = SettingsConfigDict(
        env_file=(".env" if _use_env_file else None),
        case_sensitive=True
    )


try:
    settings = Settings()
except Exception:
    # Fallback for test/collection environments where env parsing may fail
    os.environ["TEST_MODE"] = os.environ.get("TEST_MODE", "1")
    class _TestSettings(Settings):
        model_config = SettingsConfigDict(env_file=None, case_sensitive=True)
    settings = _TestSettings()
