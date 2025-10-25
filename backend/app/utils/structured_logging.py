"""
Strukturiertes Logging für Blockchain Forensics Platform

Bietet JSON-strukturierte Logs mit Kontext-Informationen für:
- Request Tracing
- Error Tracking
- Performance Monitoring
- Security Auditing
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context Variables für Request Tracing
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON-Formatter für strukturierte Logs
    
    Output Format:
    {
      "timestamp": "2025-01-10T20:00:00.123Z",
      "level": "INFO",
      "logger": "app.api.trace",
      "message": "Trace started",
      "request_id": "abc-123",
      "user_id": "user-456",
      "extra": {...}
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Request Context
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        # Exception Info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Extra Fields (z.B. duration, trace_id, etc.)
        if hasattr(record, 'extra'):
            log_data["extra"] = record.extra
        
        # Module & Function Info
        log_data["source"] = {
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "path": record.pathname
        }
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Farbiger Formatter für Development Console
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        # Format: [LEVEL] timestamp - logger - message
        formatted = (
            f"{color}[{record.levelname:8}]{reset} "
            f"{datetime.utcnow().strftime('%H:%M:%S.%f')[:-3]} - "
            f"{record.name:30} - "
            f"{record.getMessage()}"
        )
        
        # Context Info
        request_id = request_id_var.get()
        if request_id:
            formatted += f" [req={request_id[:8]}]"
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    level: str = "INFO",
    json_logs: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Konfiguriert globales Logging
    
    Args:
        level: Log Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: JSON-strukturierte Logs (Production)
        log_file: Optional log file path
    """
    log_level = getattr(logging, level.upper())
    
    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if json_logs:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ColoredConsoleFormatter())
    
    root_logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Silence noisy loggers
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with structured logging support
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Trace started", extra={"trace_id": "123", "hops": 5})
    """
    return logging.getLogger(name)


# Convenience Functions

def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """Set request context for structured logging"""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context() -> None:
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)


def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None
) -> None:
    """
    Log HTTP request with structured data
    
    Example:
        log_request(logger, "POST", "/api/v1/trace", 200, 123.45, "user-123")
    """
    logger.info(
        f"{method} {path} {status_code}",
        extra={
            "http": {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
            "user_id": user_id
        }
    )


def log_trace_event(
    logger: logging.Logger,
    event: str,
    trace_id: str,
    **kwargs: Any
) -> None:
    """
    Log trace-specific events
    
    Example:
        log_trace_event(logger, "trace_started", "abc-123", hops=5, model="fifo")
    """
    logger.info(
        f"Trace {event}: {trace_id}",
        extra={
            "trace": {
                "event": event,
                "trace_id": trace_id,
                **kwargs
            }
        }
    )


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Log security-related events
    
    Example:
        log_security_event(logger, "login_failed", user_id="user-123", ip_address="1.2.3.4")
    """
    logger.warning(
        f"Security Event: {event_type}",
        extra={
            "security": {
                "event_type": event_type,
                "user_id": user_id,
                "ip_address": ip_address,
                **kwargs
            }
        }
    )


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **kwargs: Any
) -> None:
    """
    Log performance metrics
    
    Example:
        log_performance(logger, "neo4j_query", 123.45, query="MATCH...", rows=100)
    """
    logger.info(
        f"Performance: {operation} ({duration_ms:.2f}ms)",
        extra={
            "performance": {
                "operation": operation,
                "duration_ms": duration_ms,
                **kwargs
            }
        }
    )
