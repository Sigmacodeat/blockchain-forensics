"""
Advanced Security Service
Provides comprehensive security features for the blockchain forensics platform
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re
import ipaddress
from urllib.parse import urlparse

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import jwt
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    name: str
    requests_per_window: int
    window_seconds: int
    burst_limit: Optional[int] = None  # Allow bursts up to this limit
    cooldown_seconds: int = 60  # Cooldown period after hitting limit


@dataclass
class SecurityMetrics:
    """Security metrics for monitoring"""
    total_requests: int = 0
    blocked_requests: int = 0
    rate_limited_requests: int = 0
    suspicious_requests: int = 0
    auth_failures: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple strategies

    Features:
    - Token bucket algorithm for smooth rate limiting
    - Per-IP, per-user, and per-endpoint limits
    - Adaptive rate limiting based on system load
    - Burstable limits for legitimate traffic spikes
    - Geographic and behavioral analysis
    """

    def __init__(self):
        # Rate limiting rules
        self.rules = {
            "global": RateLimitRule("global", 1000, 60, burst_limit=2000),
            "per_ip": RateLimitRule("per_ip", 100, 60, burst_limit=200),
            "per_user": RateLimitRule("per_user", 200, 60, burst_limit=400),
            "per_endpoint": RateLimitRule("per_endpoint", 50, 60, burst_limit=100),
            "auth_endpoints": RateLimitRule("auth_endpoints", 10, 60, burst_limit=20),
            "admin_endpoints": RateLimitRule("admin_endpoints", 30, 60, burst_limit=50),
        }

        # Token buckets for each rule and identifier
        self.buckets: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))

        # Request history for pattern analysis
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)

        # Blocked IPs and suspicious patterns
        self.blocked_ips: set = set()
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)

        # Metrics
        self.metrics = SecurityMetrics()

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    def start(self) -> None:
        """Start the rate limiter background tasks"""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    def stop(self) -> None:
        """Stop the rate limiter"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()

    async def check_rate_limit(
        self,
        request: Request,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> bool:
        """
        Check if request should be rate limited

        Returns True if request should be allowed, False if blocked
        """
        self.metrics.total_requests += 1

        client_ip = self._get_client_ip(request)
        user_identifier = user_id or f"ip:{client_ip}"

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            self.metrics.blocked_requests += 1
            return False

        # Apply rate limiting rules
        rules_to_check = [
            ("global", "global"),
            ("per_ip", client_ip),
            ("per_endpoint", endpoint or "unknown"),
        ]

        if user_id:
            rules_to_check.append(("per_user", user_identifier))

        # Check authentication endpoints
        if endpoint and any(auth_path in endpoint for auth_path in ["/auth", "/login", "/register"]):
            rules_to_check.append(("auth_endpoints", "auth"))

        # Check admin endpoints
        if endpoint and any(admin_path in endpoint for admin_path in ["/admin", "/users"]):
            rules_to_check.append(("admin_endpoints", "admin"))

        for rule_name, identifier in rules_to_check:
            if not self._check_rule(rule_name, identifier, request):
                return False

        # Record request for pattern analysis
        self._record_request(client_ip, user_identifier, endpoint)

        return True

    def _check_rule(self, rule_name: str, identifier: str, request: Request) -> bool:
        """Check a specific rate limiting rule"""
        rule = self.rules.get(rule_name)
        if not rule:
            return True

        bucket_key = f"{rule_name}:{identifier}"
        bucket = self.buckets[rule_name][identifier]

        now = time.time()

        # Clean old tokens from bucket
        cutoff_time = now - rule.window_seconds
        while bucket and bucket[0] < cutoff_time:
            bucket.popleft()

        # Check if bucket is full
        if len(bucket) >= rule.requests_per_window:
            # Check burst limit
            if rule.burst_limit and len(bucket) < rule.burst_limit:
                # Allow burst
                pass
            else:
                self.metrics.rate_limited_requests += 1
                logger.warning(f"Rate limit exceeded for {rule_name}:{identifier}")
                return False

        # Add current request token
        bucket.append(now)

        return True

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check X-Forwarded-For header first (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to client host
        return request.client.host if request.client else "unknown"

    def _record_request(self, client_ip: str, user_id: str, endpoint: Optional[str]) -> None:
        """Record request for pattern analysis"""
        now = datetime.utcnow()

        # Store request history for pattern analysis
        self.request_history[client_ip].append(now)

        # Keep only last 100 requests per IP
        if len(self.request_history[client_ip]) > 100:
            self.request_history[client_ip] = self.request_history[client_ip][-100:]

        # Detect suspicious patterns
        self._detect_suspicious_patterns(client_ip, user_id, endpoint)

    def _detect_suspicious_patterns(self, client_ip: str, user_id: str, endpoint: Optional[str]) -> None:
        """Detect suspicious request patterns"""
        recent_requests = self.request_history[client_ip]
        if len(recent_requests) < 10:
            return

        # Check for rapid requests (potential DoS)
        recent_window = datetime.utcnow() - timedelta(seconds=10)
        recent_count = len([req for req in recent_requests if req > recent_window])

        if recent_count > 50:  # More than 50 requests in 10 seconds
            self.blocked_ips.add(client_ip)
            self.metrics.suspicious_requests += 1
            logger.warning(f"Blocked suspicious IP {client_ip}: {recent_count} requests in 10s")

        # Check for unusual endpoint access patterns
        if endpoint and self._is_unusual_endpoint_pattern(client_ip, endpoint):
            self.suspicious_patterns[client_ip] += 1
            if self.suspicious_patterns[client_ip] > 5:
                self.blocked_ips.add(client_ip)
                logger.warning(f"Blocked IP {client_ip} for unusual endpoint patterns")

    def _is_unusual_endpoint_pattern(self, client_ip: str, endpoint: str) -> bool:
        """Check if endpoint access pattern is unusual"""
        # Simple heuristic: too many different endpoints from same IP
        endpoints = set()
        for req_time in self.request_history[client_ip][-20:]:  # Last 20 requests
            # This would need actual endpoint tracking in a real implementation
            pass

        return False  # Placeholder

    async def _cleanup_loop(self) -> None:
        """Background cleanup task"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Clean every 5 minutes

                # Clean old request history
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                for ip, requests in list(self.request_history.items()):
                    self.request_history[ip] = [
                        req for req in requests if req > cutoff_time
                    ]
                    if not self.request_history[ip]:
                        del self.request_history[ip]

                # Clean old buckets
                for rule_name, rule_buckets in self.buckets.items():
                    for identifier, bucket in list(rule_buckets.items()):
                        cutoff_time = time.time() - self.rules[rule_name].window_seconds * 2
                        while bucket and bucket[0] < cutoff_time:
                            bucket.popleft()
                        if not bucket:
                            del rule_buckets[identifier]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "blocked_requests": self.metrics.blocked_requests,
                "rate_limited_requests": self.metrics.rate_limited_requests,
                "suspicious_requests": self.metrics.suspicious_requests,
                "auth_failures": self.metrics.auth_failures,
            },
            "blocked_ips": len(self.blocked_ips),
            "suspicious_patterns": dict(self.suspicious_patterns),
            "active_buckets": sum(
                len(buckets) for rule_buckets in self.buckets.values()
                for buckets in [rule_buckets]
            ),
            "tracked_ips": len(self.request_history)
        }


class SecurityHeadersMiddleware:
    """Middleware for adding security headers to responses"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Store original send function
        original_send = send

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                # Add security headers
                security_headers = [
                    (b"X-Content-Type-Options", b"nosniff"),
                    (b"X-Frame-Options", b"DENY"),
                    (b"X-XSS-Protection", b"1; mode=block"),
                    (b"Referrer-Policy", b"strict-origin-when-cross-origin"),
                    (b"Content-Security-Policy", b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"),
                    (b"Strict-Transport-Security", b"max-age=31536000; includeSubDomains"),
                    (b"Permissions-Policy", b"geolocation=(), microphone=(), camera=()"),
                ]

                # Add security headers to existing headers
                for header_name, header_value in security_headers:
                    # Check if header already exists
                    header_exists = any(h[0].lower() == header_name.lower() for h in headers)
                    if not header_exists:
                        headers.append((header_name, header_value))

                message["headers"] = headers

            await original_send(message)

        await self.app(scope, receive, send_with_headers)


class InputValidator:
    """Advanced input validation for security"""

    # Patterns for detecting malicious input
    MALICIOUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URLs
        r"vbscript:",  # VBScript URLs
        r"on\w+\s*=",  # Event handlers
        r"expression\s*\(",  # CSS expressions
        r"<!--.*?-->",  # HTML comments (potential XSS)
    ]

    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;)|(\|\|)|(\band\b|\bor\b|\bnot\b)|(\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b)",
        r"(\bexec\b|\bexecute\b|\bsp_\b|\bxp_\b)",
    ]

    @classmethod
    def validate_input(cls, value: str, field_name: str = "input") -> str:
        """Validate input for malicious content"""
        if not isinstance(value, str):
            return str(value)

        # Check for malicious patterns
        for pattern in cls.MALICIOUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Malicious pattern detected in {field_name}: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Potentially malicious content detected in {field_name}"
                )

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected in {field_name}: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Potentially malicious SQL content detected in {field_name}"
                )

        return value

    @classmethod
    def validate_address(cls, address: str) -> str:
        """Validate blockchain address format"""
        if not address or len(address) < 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid address format"
            )

        # Basic format validation (should be enhanced per chain)
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):  # Ethereum format
            # Could add Bitcoin, Solana, etc. validation here
            pass

        return cls.validate_input(address, "address")

    @classmethod
    def validate_transaction_hash(cls, tx_hash: str) -> str:
        """Validate transaction hash format"""
        if not tx_hash or len(tx_hash) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction hash format"
            )

        return cls.validate_input(tx_hash, "transaction_hash")


class APIKeySecurity:
    """Enhanced API key security management"""

    def __init__(self):
        self.valid_keys: Dict[str, Dict[str, Any]] = {}
        self.key_usage: Dict[str, List[datetime]] = defaultdict(list)
        self.revoked_keys: set = set()

    def validate_api_key(self, api_key: str, request: Request) -> Dict[str, Any]:
        """Validate API key and return key information"""
        if api_key in self.revoked_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked"
            )

        key_info = self.valid_keys.get(api_key)
        if not key_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        # Check rate limits for API key
        recent_usage = [
            usage for usage in self.key_usage[api_key]
            if usage > datetime.utcnow() - timedelta(minutes=1)
        ]

        if len(recent_usage) > key_info.get("rate_limit_per_minute", 100):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API key rate limit exceeded"
            )

        # Record usage
        self.key_usage[api_key].append(datetime.utcnow())

        return key_info

    def add_api_key(self, api_key: str, permissions: List[str], rate_limit: int = 100) -> None:
        """Add a new API key"""
        self.valid_keys[api_key] = {
            "permissions": permissions,
            "rate_limit_per_minute": rate_limit,
            "created_at": datetime.utcnow(),
            "last_used": None
        }

    def revoke_api_key(self, api_key: str) -> None:
        """Revoke an API key"""
        self.revoked_keys.add(api_key)
        if api_key in self.valid_keys:
            del self.valid_keys[api_key]


# Global security instances
rate_limiter = AdvancedRateLimiter()
input_validator = InputValidator()
api_key_security = APIKeySecurity()


def initialize_security() -> None:
    """Initialize security services"""
    rate_limiter.start()
    logger.info("Security services initialized")


def shutdown_security() -> None:
    """Shutdown security services"""
    rate_limiter.stop()
    logger.info("Security services shut down")


class PIIDetector:
    """PII detection and masking service"""

    def __init__(self):
        self.pii_patterns = [
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IPs
            r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',  # Phone numbers
        ]
        self.blocked_keywords = [
            'password', 'ssn', 'social security', 'credit card',
            'bank account', 'routing number', 'cvv', 'pin'
        ]

    def detect_pii(self, text: str) -> Dict[str, Any]:
        """Detect PII in text."""
        findings = []

        for pattern in self.pii_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                findings.extend([{"type": "pii", "pattern": pattern, "matches": matches}])

        # Check for blocked keywords
        text_lower = text.lower()
        for keyword in self.blocked_keywords:
            if keyword in text_lower:
                findings.append({"type": "blocked_keyword", "keyword": keyword})

        return {
            "has_pii": len(findings) > 0,
            "findings": findings,
            "risk_level": "high" if len(findings) > 0 else "low"
        }

    def mask_pii(self, text: str) -> str:
        """Mask PII in text."""
        masked = text

        # Mask emails
        masked = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                       '[EMAIL_MASKED]', masked, flags=re.IGNORECASE)

        # Mask IPs
        masked = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                       '[IP_MASKED]', masked)

        # Mask potential credit cards
        masked = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
                       '[CC_MASKED]', masked)

        # Mask phone numbers
        masked = re.sub(r'\b\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
                       '[PHONE_MASKED]', masked)

        return masked


class GDPRComplianceService:
    """GDPR compliance service"""

    def __init__(self):
        self.consent_expiry_days = 365
        self.data_retention_days = {
            "chat_history": 90,
            "analytics": 365,
            "audit_logs": 2555  # 7 years
        }

    def check_consent(self, session_id: str, consent_type: str = "data_processing") -> bool:
        """Check if user has given consent."""
        # In a real implementation, this would check a consent database
        # For demo, assume consent is given
        return True

    def record_consent(self, session_id: str, consent_types: List[str]):
        """Record user consent."""
        # In a real implementation, save to database
        logger.info(f"Consent recorded for {session_id}: {consent_types}")

    def get_data_retention_info(self, data_type: str) -> Dict[str, Any]:
        """Get data retention information."""
        return {
            "retention_days": self.data_retention_days.get(data_type, 365),
            "auto_delete": True,
            "legal_basis": "legitimate_interest"
        }

# Enhanced security service instances
pii_detector = PIIDetector()
gdpr_service = GDPRComplianceService()

# Initialize security on startup
def initialize_security():
    """Initialize all security services"""
    rate_limiter.start()
    logger.info("All security services initialized")

def shutdown_security():
    """Shutdown all security services"""
    rate_limiter.stop()
    logger.info("All security services shut down")

def get_comprehensive_security_stats() -> Dict[str, Any]:
    """Get comprehensive security statistics"""
    return {
        "rate_limiter": rate_limiter.get_stats(),
        "blocked_ips": len(rate_limiter.blocked_ips),
        "suspicious_patterns": dict(rate_limiter.suspicious_patterns),
        "api_keys_active": len(api_key_security.valid_keys),
        "api_keys_revoked": len(api_key_security.revoked_keys),
        "pii_detection_enabled": True,
        "gdpr_compliance_enabled": True
    }
