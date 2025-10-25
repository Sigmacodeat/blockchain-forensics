"""
Performance Monitoring & Observability Service
Umfassende Lösung für System-Monitoring, Logging und Performance-Optimierung
"""

import logging
import time
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import json


logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Service für Performance-Monitoring und -Optimierung"""

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[Dict[str, Any]] = []
        self.slo_definitions: Dict[str, Dict[str, Any]] = {
            "api_response_time": {"threshold": 1000, "unit": "ms", "severity": "warning"},
            "database_query_time": {"threshold": 500, "unit": "ms", "severity": "warning"},
            "alert_processing_time": {"threshold": 5000, "unit": "ms", "severity": "critical"},
            "memory_usage": {"threshold": 80, "unit": "%", "severity": "warning"},
            "cpu_usage": {"threshold": 70, "unit": "%", "severity": "warning"},
            "error_rate": {"threshold": 5, "unit": "%", "severity": "critical"}
        }

        # Performance thresholds
        self.thresholds = {
            "slow_query_ms": 1000,
            "high_memory_percent": 80,
            "high_cpu_percent": 70,
            "error_rate_percent": 5,
            "timeout_seconds": 30
        }

        # Start background monitoring
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.monitoring_thread.start()

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        timestamp = datetime.utcnow()
        metric_data = {
            "name": name,
            "value": value,
            "timestamp": timestamp,
            "tags": tags or {}
        }

        self.metrics[name].append(metric_data)

        # Check SLO compliance
        self._check_slo_compliance(name, value, timestamp)

        logger.debug(f"Recorded metric {name}: {value}")

    def _check_slo_compliance(self, metric_name: str, value: float, timestamp: datetime):
        """Check if metric violates SLO definitions"""
        if metric_name in self.slo_definitions:
            slo = self.slo_definitions[metric_name]
            threshold = slo["threshold"]

            if value > threshold:
                alert = {
                    "type": "slo_violation",
                    "metric": metric_name,
                    "value": value,
                    "threshold": threshold,
                    "severity": slo["severity"],
                    "timestamp": timestamp,
                    "description": f"SLO violation for {metric_name}: {value} > {threshold} {slo['unit']}"
                }

                self.alerts.append(alert)

                # Log the violation
                logger.warning(f"SLO VIOLATION: {alert['description']}")

                # Trigger alerting if needed
                self._trigger_performance_alert(alert)

    def _trigger_performance_alert(self, alert: Dict[str, Any]):
        """Trigger alerts for performance issues"""
        # In a real system, this would integrate with alerting systems
        # For now, just log the alert
        logger.error(f"PERFORMANCE ALERT: {alert['description']}")

    def _background_monitoring(self):
        """Background monitoring of system metrics"""
        while self.monitoring_active:
            try:
                # System metrics
                self._record_system_metrics()

                # Custom performance checks
                self._check_performance_anomalies()

                time.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(30)  # Wait longer on errors

    def _record_system_metrics(self):
        """Record system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("cpu_usage_percent", cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric("memory_usage_percent", memory.percent)
            self.record_metric("memory_available_mb", memory.available / 1024 / 1024)

            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric("disk_usage_percent", disk.percent)

            # Network I/O
            net_io = psutil.net_io_counters()
            self.record_metric("network_bytes_sent", net_io.bytes_sent)
            self.record_metric("network_bytes_recv", net_io.bytes_recv)

            # Process info
            process = psutil.Process()
            self.record_metric("process_memory_mb", process.memory_info().rss / 1024 / 1024)
            self.record_metric("process_cpu_percent", process.cpu_percent())
            self.record_metric("process_threads", process.num_threads())

        except Exception as e:
            logger.error(f"Error recording system metrics: {e}")

    def _check_performance_anomalies(self):
        """Check for performance anomalies"""
        try:
            # Check for high memory usage
            recent_memory = [m["value"] for m in list(self.metrics["memory_usage_percent"])][-10:]
            if recent_memory and max(recent_memory) > self.thresholds["high_memory_percent"]:
                self.record_metric("memory_anomaly", 1.0, {"type": "high_usage"})

            # Check for high CPU usage
            recent_cpu = [m["value"] for m in list(self.metrics["cpu_usage_percent"])][-10:]
            if recent_cpu and max(recent_cpu) > self.thresholds["high_cpu_percent"]:
                self.record_metric("cpu_anomaly", 1.0, {"type": "high_usage"})

            # Check for increasing response times
            if len(self.metrics["api_response_time"]) >= 10:
                recent_times = [m["value"] for m in list(self.metrics["api_response_time"])][-10:]
                if len(set(recent_times)) > 1:  # Avoid division by zero
                    trend = (recent_times[-1] - recent_times[0]) / len(recent_times)
                    if trend > 100:  # Increasing trend > 100ms per sample
                        self.record_metric("response_time_trend", trend, {"type": "increasing"})

        except Exception as e:
            logger.error(f"Error checking performance anomalies: {e}")

    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        summary = {
            "time_window_minutes": time_window_minutes,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": {},
            "alerts": len([a for a in self.alerts if a["timestamp"] > cutoff_time]),
            "slo_violations": len([a for a in self.alerts if a["type"] == "slo_violation" and a["timestamp"] > cutoff_time])
        }

        for metric_name, metric_data in self.metrics.items():
            recent_metrics = [m for m in metric_data if m["timestamp"] > cutoff_time]

            if recent_metrics:
                values = [m["value"] for m in recent_metrics]

                summary["metrics"][metric_name] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1] if values else None,
                    "trend": self._calculate_trend(values)
                }

        return summary

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for values"""
        if len(values) < 2:
            return "insufficient_data"

        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

        if second_half > first_half * 1.1:
            return "increasing"
        elif second_half < first_half * 0.9:
            return "decreasing"
        else:
            return "stable"

    def get_slo_report(self) -> Dict[str, Any]:
        """Generate SLO compliance report"""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "slo_definitions": self.slo_definitions,
            "compliance": {},
            "violations": []
        }

        for metric_name, slo_def in self.slo_definitions.items():
            if metric_name in self.metrics and len(self.metrics[metric_name]) > 0:
                recent_values = [m["value"] for m in self.metrics[metric_name][-100:]]  # Last 100 samples

                if recent_values:
                    violation_count = sum(1 for v in recent_values if v > slo_def["threshold"])
                    compliance_rate = 1 - (violation_count / len(recent_values))

                    report["compliance"][metric_name] = {
                        "compliance_rate": compliance_rate,
                        "total_samples": len(recent_values),
                        "violations": violation_count,
                        "threshold": slo_def["threshold"],
                        "unit": slo_def["unit"]
                    }

        # Add recent violations
        recent_violations = [a for a in self.alerts if a["type"] == "slo_violation"][-10:]
        report["violations"] = recent_violations

        return report

    def export_metrics(self, format: str = "json", time_window_minutes: int = 60) -> str:
        """Export metrics data for analysis"""
        summary = self.get_metrics_summary(time_window_minutes)

        if format.lower() == "json":
            return json.dumps(summary, indent=2, ensure_ascii=False, default=str)
        elif format.lower() == "csv":
            # Simple CSV export for metrics
            lines = ["timestamp,metric_name,value,tags"]

            for metric_name, metric_data in self.metrics.items():
                for sample in metric_data:
                    if sample["timestamp"] > datetime.utcnow() - timedelta(minutes=time_window_minutes):
                        tags_str = ";".join(f"{k}:{v}" for k, v in sample.get("tags", {}).items())
                        lines.append(f"{sample['timestamp']},{metric_name},{sample['value']},{tags_str}")

            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def cleanup_old_data(self, max_age_days: int = 7):
        """Clean up old metrics and alert data"""
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)

        # Clean metrics
        for metric_name in self.metrics:
            self.metrics[metric_name] = deque(
                [m for m in self.metrics[metric_name] if m["timestamp"] > cutoff_time],
                maxlen=1000
            )

        # Clean alerts
        self.alerts = [a for a in self.alerts if a["timestamp"] > cutoff_time]

        logger.info(f"Cleaned up old monitoring data (older than {max_age_days} days)")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


class PerformanceTracer:
    """Distributed tracing for performance analysis"""

    def __init__(self):
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.active_traces: Dict[str, Dict[str, Any]] = {}

    def start_trace(self, trace_id: str, operation: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Start a new trace"""
        span_id = f"{trace_id}_span_{len(self.active_traces)}"

        trace_data = {
            "trace_id": trace_id,
            "span_id": span_id,
            "operation": operation,
            "start_time": time.time(),
            "tags": tags or {},
            "events": []
        }

        self.active_traces[span_id] = trace_data

        return span_id

    def end_trace(self, span_id: str, status: str = "success", error: Optional[str] = None):
        """End an active trace"""
        if span_id not in self.active_traces:
            logger.warning(f"Attempted to end non-existent trace: {span_id}")
            return

        trace_data = self.active_traces[span_id]
        trace_data["end_time"] = time.time()
        trace_data["duration_ms"] = (trace_data["end_time"] - trace_data["start_time"]) * 1000
        trace_data["status"] = status
        trace_data["error"] = error

        # Move to completed traces
        self.traces[span_id] = trace_data
        del self.active_traces[span_id]

        # Record performance metric
        performance_monitor.record_metric(
            "trace_duration_ms",
            trace_data["duration_ms"],
            {"operation": trace_data["operation"], "status": status}
        )

        logger.debug(f"Trace completed: {trace_data.get('operation', 'unknown')} took {trace_data['duration_ms']:.2f}ms")

    def add_trace_event(self, span_id: str, event: str, metadata: Optional[Dict[str, Any]] = None):
        """Add an event to an active trace"""
        if span_id in self.active_traces:
            event_data = {
                "timestamp": time.time(),
                "event": event,
                "metadata": metadata or {}
            }
            self.active_traces[span_id]["events"].append(event_data)

    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of recent traces"""
        recent_traces = {}
        cutoff_time = time.time() - 3600  # Last hour

        for span_id, trace_data in self.traces.items():
            if trace_data["start_time"] > cutoff_time:
                recent_traces[span_id] = {
                    "operation": trace_data["operation"],
                    "duration_ms": trace_data["duration_ms"],
                    "status": trace_data["status"],
                    "start_time": trace_data["start_time"]
                }

        # Group by operation
        operation_stats = defaultdict(list)
        for trace in recent_traces.values():
            operation_stats[trace["operation"]].append(trace["duration_ms"])

        summary = {
            "total_traces_1h": len(recent_traces),
            "active_traces": len(self.active_traces),
            "operation_stats": {}
        }

        for operation, durations in operation_stats.items():
            summary["operation_stats"][operation] = {
                "count": len(durations),
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations)
            }

        return summary


# Global tracer instance
performance_tracer = PerformanceTracer()


# Decorator for automatic tracing
def trace_operation(operation_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator for automatic operation tracing"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            trace_id = f"{operation_name}_{int(time.time() * 1000)}"
            span_id = performance_tracer.start_trace(trace_id, operation_name, tags)

            try:
                result = await func(*args, **kwargs)
                performance_tracer.end_trace(span_id, "success")
                return result
            except Exception as e:
                performance_tracer.end_trace(span_id, "error", str(e))
                raise

        def sync_wrapper(*args, **kwargs):
            trace_id = f"{operation_name}_{int(time.time() * 1000)}"
            span_id = performance_tracer.start_trace(trace_id, operation_name, tags)

            try:
                result = func(*args, **kwargs)
                performance_tracer.end_trace(span_id, "success")
                return result
            except Exception as e:
                performance_tracer.end_trace(span_id, "error", str(e))
                raise

        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Middleware for automatic API tracing
class PerformanceTracingMiddleware:
    """Middleware for automatic API endpoint tracing"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info
        path = scope.get("path", "")
        method = scope.get("method", "")

        operation_name = f"api_{method.lower()}_{path.replace('/', '_').strip('_')}"

        # Start trace
        trace_id = f"{operation_name}_{int(time.time() * 1000)}"
        span_id = performance_tracer.start_trace(trace_id, operation_name)

        # Add request start event
        performance_tracer.add_trace_event(span_id, "request_started", {
            "method": method,
            "path": path
        })

        # Track response
        original_send = send

        async def traced_send(message):
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                performance_tracer.add_trace_event(span_id, "response_started", {
                    "status_code": status_code
                })

                # End trace based on status
                status = "success" if 200 <= status_code < 400 else "error"
                performance_tracer.end_trace(span_id, status)

            await original_send(message)

        await self.app(scope, receive, traced_send)
