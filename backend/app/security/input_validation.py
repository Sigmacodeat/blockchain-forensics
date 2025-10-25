"""
Input Validation Framework
==========================
OWASP-compliant input validation and sanitization.
"""

import re
from typing import List, Optional
from pydantic import BaseModel, validator
import bleach
from fastapi import HTTPException

class SanitizedString(str):
    """String with HTML sanitization"""
    
    def __new__(cls, value: str, allowed_tags: Optional[List[str]] = None):
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        
        # Basic length check
        if len(value) > 10000:  # Max 10KB
            raise ValueError("String too long")
        
        # Sanitize HTML
        allowed_tags = allowed_tags or []
        sanitized = bleach.clean(value, tags=allowed_tags, strip=True)
        
        return str.__new__(cls, sanitized)

class AddressValidation:
    """Blockchain address validation"""
    
    ETH_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')
    BTC_PATTERN = re.compile(r'^(1[1-9A-HJ-NP-Za-km-z]{25,34}|3[1-9A-HJ-NP-Za-km-z]{25,34}|bc1[a-z0-9]{39,59})$')
    
    @staticmethod
    def is_valid_ethereum(address: str) -> bool:
        return bool(AddressValidation.ETH_PATTERN.match(address))
    
    @staticmethod
    def is_valid_bitcoin(address: str) -> bool:
        return bool(AddressValidation.BTC_PATTERN.match(address))
    
    @staticmethod
    def is_valid_address(address: str, chain: str = "ethereum") -> bool:
        if chain.lower() == "ethereum":
            return AddressValidation.is_valid_ethereum(address)
        elif chain.lower() == "bitcoin":
            return AddressValidation.is_valid_bitcoin(address)
        return False

class TransactionValidation:
    """Transaction hash validation"""
    
    ETH_TX_PATTERN = re.compile(r'^0x[a-fA-F0-9]{64}$')
    BTC_TX_PATTERN = re.compile(r'^[a-fA-F0-9]{64}$')
    
    @staticmethod
    def is_valid_ethereum_tx(tx_hash: str) -> bool:
        return bool(TransactionValidation.ETH_TX_PATTERN.match(tx_hash))
    
    @staticmethod
    def is_valid_bitcoin_tx(tx_hash: str) -> bool:
        return bool(TransactionValidation.BTC_TX_PATTERN.match(tx_hash))

class InputSanitizer:
    """General input sanitization"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Sanitize general text input"""
        if not isinstance(text, str):
            raise HTTPException(status_code=400, detail="Input must be string")
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email addresses"""
        email = InputSanitizer.sanitize_text(email, 254)  # RFC 5321 limit
        
        # Basic email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        return email
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URLs"""
        url = InputSanitizer.sanitize_text(url, 2000)
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse and validate URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError("Invalid URL")
        except:
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        return url

class APIRequestValidation(BaseModel):
    """Base validation for API requests"""
    
    @validator('*', pre=True)
    def validate_input(cls, v):
        if isinstance(v, str):
            return InputSanitizer.sanitize_text(v)
        return v

# Validation schemas for common endpoints
class TraceRequestValidation(APIRequestValidation):
    address: str
    chain: str = "ethereum"
    depth: int = 3
    
    @validator('address')
    def validate_address(cls, v, values):
        chain = values.get('chain', 'ethereum')
        if not AddressValidation.is_valid_address(v, chain):
            raise ValueError(f"Invalid {chain} address format")
        return v
    
    @validator('depth')
    def validate_depth(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Depth must be between 1 and 10")
        return v

class RiskRequestValidation(APIRequestValidation):
    address: str
    chain: str = "ethereum"
    
    @validator('address')
    def validate_address(cls, v, values):
        chain = values.get('chain', 'ethereum')
        if not AddressValidation.is_valid_address(v, chain):
            raise ValueError(f"Invalid {chain} address format")
        return v

# SQL Injection prevention
class SQLInjectionCheck:
    """Basic SQL injection detection"""
    
    DANGEROUS_PATTERNS = [
        r';\s*(drop|delete|update|insert|alter|create|truncate)\s',
        r'union\s+select',
        r'--',
        r'/\*.*\*/',
        r'xp_cmdshell',
        r'exec\s*\(',
    ]
    
    @staticmethod
    def check_input(text: str) -> bool:
        """Return True if input appears safe"""
        text_lower = text.lower()
        for pattern in SQLInjectionCheck.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        return True

# XSS Prevention
class XSSPrevention:
    """XSS attack prevention"""
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        """Sanitize HTML content"""
        allowed_tags = ['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li']
        allowed_attrs = {'a': ['href', 'title']}
        
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
