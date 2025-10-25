"""
Security Utilities
==================

Input validation, sanitization, and security helpers.
"""

import re
import html
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecurityError(ValueError):
    """Security validation error"""
    pass


def validate_eth_address(address: str) -> bool:
    """
    Validate Ethereum address format
    
    Args:
        address: Address to validate (0x...)
    
    Returns:
        True if valid format
    """
    if not address:
        return False
    
    # Must start with 0x and have 40 hex characters
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def validate_string_length(text: str, min_len: int = 1, max_len: int = 10000) -> bool:
    """
    Validate string length
    
    Args:
        text: String to validate
        min_len: Minimum length
        max_len: Maximum length
    
    Returns:
        True if within bounds
    """
    if not text:
        return min_len == 0
    
    length = len(text)
    return min_len <= length <= max_len


def sanitize_html(text: str) -> str:
    """
    Remove HTML/XSS from text
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text (HTML entities escaped)
    """
    if not text:
        return ""
    
    # Escape HTML entities
    return html.escape(text)


def validate_bitcoin_address(address: str) -> bool:
    """
    Validate Bitcoin address format
    
    Supports: P2PKH (1...), P2SH (3...), Bech32 (bc1...)
    """
    if not address:
        return False
    
    # P2PKH or P2SH
    legacy_pattern = r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'
    # Bech32
    bech32_pattern = r'^(bc1)[a-z0-9]{25,62}$'
    
    return bool(re.match(legacy_pattern, address) or re.match(bech32_pattern, address))


def validate_url(url: str, allowed_schemes: list = None) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])
    
    Returns:
        True if valid
    """
    if not url:
        return False
    
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    # Basic URL pattern
    pattern = r'^(?:(?:' + '|'.join(allowed_schemes) + r'):\/\/)(?:[^\s@\/]+@)?(?:[^\s:\/]+)(?::\d+)?(?:\/[^\s]*)?$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal
    
    Args:
        filename: Filename to sanitize
    
    Returns:
        Safe filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove parent directory references
    filename = filename.replace('..', '_')
    
    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename or "unnamed"


def mask_sensitive_data(text: str, pattern: str = r'\b[\w.%+-]+@[\w.-]+\.[A-Z|a-z]{2,}\b') -> str:
    """
    Mask sensitive data in text (emails, etc.)
    
    Args:
        text: Text to mask
        pattern: Regex pattern to match
    
    Returns:
        Text with sensitive data masked
    """
    if not text:
        return ""
    
    return re.sub(pattern, '***REDACTED***', text)
