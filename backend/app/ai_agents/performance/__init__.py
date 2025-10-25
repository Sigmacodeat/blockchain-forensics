"""
Performance Optimization Module for AI Agent Tools.
Includes caching, parallel execution, and predictive pre-loading.
"""

from .tool_cache import tool_cache, cached_tool, ToolCache
from .parallel_executor import parallel_executor, ParallelToolExecutor

__all__ = [
    "tool_cache",
    "cached_tool",
    "ToolCache",
    "parallel_executor",
    "ParallelToolExecutor",
]
