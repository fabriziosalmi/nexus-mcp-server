# -*- coding: utf-8 -*-
# monitoring.py - Prometheus monitoring for Nexus MCP Server
import time
import threading
from typing import Optional
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST


class PrometheusMonitoring:
    """
    Prometheus monitoring class for MCP server metrics.
    Provides counters, histograms, and gauges for tool execution monitoring.
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize Prometheus metrics with optional custom registry."""
        self.registry = registry or CollectorRegistry()
        
        # Counter: Total number of tool calls by tool name and status
        self.tool_calls_total = Counter(
            'mcp_tool_calls_total',
            'Total number of MCP tool calls',
            ['tool_name', 'status'],
            registry=self.registry
        )
        
        # Histogram: Duration of tool execution in seconds
        self.tool_duration_seconds = Histogram(
            'mcp_tool_duration_seconds',
            'Duration of MCP tool execution in seconds',
            ['tool_name'],
            registry=self.registry,
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))
        )
        
        # Gauge: Number of currently active sessions
        self.active_sessions = Gauge(
            'mcp_active_sessions',
            'Number of currently active MCP sessions',
            registry=self.registry
        )
        
        # Thread-safe session tracking
        self._sessions_lock = threading.Lock()
        self._active_session_count = 0
    
    def increment_session(self):
        """Increment the active sessions counter thread-safely."""
        with self._sessions_lock:
            self._active_session_count += 1
            self.active_sessions.set(self._active_session_count)
    
    def decrement_session(self):
        """Decrement the active sessions counter thread-safely."""
        with self._sessions_lock:
            self._active_session_count = max(0, self._active_session_count - 1)
            self.active_sessions.set(self._active_session_count)
    
    @contextmanager
    def track_session(self):
        """Context manager to track a session lifecycle."""
        self.increment_session()
        try:
            yield
        finally:
            self.decrement_session()
    
    @contextmanager
    def track_tool_execution(self, tool_name: str):
        """
        Context manager to track tool execution time and status.
        
        Args:
            tool_name: Name of the tool being executed
            
        Yields:
            A context object that can be used to set the execution status
        """
        start_time = time.time()
        
        class ExecutionContext:
            def __init__(self, monitoring_instance, tool_name, start_time):
                self.monitoring = monitoring_instance
                self.tool_name = tool_name
                self.start_time = start_time
                self.status = "success"  # default status
                
            def set_status(self, status: str):
                """Set the execution status (success, error, timeout, etc.)"""
                self.status = status
        
        context = ExecutionContext(self, tool_name, start_time)
        
        try:
            yield context
        except Exception:
            context.set_status("error")
            raise
        finally:
            # Record the duration
            duration = time.time() - start_time
            self.tool_duration_seconds.labels(tool_name=tool_name).observe(duration)
            
            # Record the call with status
            self.tool_calls_total.labels(tool_name=tool_name, status=context.status).inc()
    
    def record_tool_call(self, tool_name: str, status: str, duration: Optional[float] = None):
        """
        Manually record a tool call (alternative to context manager).
        
        Args:
            tool_name: Name of the tool
            status: Execution status (success, error, timeout, etc.)
            duration: Execution duration in seconds (optional)
        """
        self.tool_calls_total.labels(tool_name=tool_name, status=status).inc()
        
        if duration is not None:
            self.tool_duration_seconds.labels(tool_name=tool_name).observe(duration)
    
    def get_metrics(self) -> bytes:
        """
        Generate metrics in Prometheus format.
        
        Returns:
            Metrics data in Prometheus exposition format
        """
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """
        Get the appropriate content type for Prometheus metrics.
        
        Returns:
            Content type string for HTTP response
        """
        return CONTENT_TYPE_LATEST
    
    def get_current_sessions(self) -> int:
        """Get the current number of active sessions."""
        with self._sessions_lock:
            return self._active_session_count


# Global monitoring instance
_global_monitoring: Optional[PrometheusMonitoring] = None


def get_monitoring() -> PrometheusMonitoring:
    """
    Get the global monitoring instance, creating it if needed.
    
    Returns:
        Global PrometheusMonitoring instance
    """
    global _global_monitoring
    if _global_monitoring is None:
        _global_monitoring = PrometheusMonitoring()
    return _global_monitoring


def initialize_monitoring(registry: Optional[CollectorRegistry] = None) -> PrometheusMonitoring:
    """
    Initialize the global monitoring instance with an optional custom registry.
    
    Args:
        registry: Optional Prometheus registry to use
        
    Returns:
        Initialized PrometheusMonitoring instance
    """
    global _global_monitoring
    _global_monitoring = PrometheusMonitoring(registry)
    return _global_monitoring