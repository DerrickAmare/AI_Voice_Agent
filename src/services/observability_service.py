"""
Observability service for metrics, logging, and monitoring.
Provides structured logging and metrics collection without requiring a database.
"""

import time
from typing import Dict, List, Optional, Any, Counter
from datetime import datetime, timedelta
from collections import defaultdict, deque
import structlog
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, generate_latest
from pydantic import BaseModel

from .redis_state_service import RedisStateService

logger = structlog.get_logger()

class MetricEvent(BaseModel):
    """Individual metric event"""
    name: str
    value: float
    labels: Dict[str, str] = {}
    timestamp: datetime

class CallMetrics(BaseModel):
    """Call-specific metrics"""
    call_id: str
    phone_hash: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: str  # 'started', 'completed', 'failed'
    adversarial_score: float = 0.0
    fields_extracted: int = 0
    webhook_delivered: bool = False
    webhook_delivery_time_ms: Optional[int] = None

class ObservabilityService:
    """Service for collecting and exposing metrics"""
    
    def __init__(self, redis_service: RedisStateService):
        self.redis_service = redis_service
        self.logger = logger.bind(service="observability")
        
        # In-memory metrics storage (for demo purposes)
        self.call_metrics: Dict[str, CallMetrics] = {}
        self.recent_events: deque = deque(maxlen=1000)  # Keep last 1000 events
        
        # Prometheus metrics
        self.setup_prometheus_metrics()
        
        # System counters
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        
    def setup_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        # Clear any existing metrics to avoid collisions
        from prometheus_client import REGISTRY, CollectorRegistry
        
        # Create a new registry for this instance to avoid conflicts
        self.registry = CollectorRegistry()
        
        # Call metrics
        self.calls_started = PrometheusCounter(
            'calls_started_total', 
            'Total number of calls started',
            ['status'],
            registry=self.registry
        )
        
        self.calls_completed = PrometheusCounter(
            'calls_completed_total', 
            'Total number of calls completed',
            ['status', 'adversarial_level'],
            registry=self.registry
        )
        
        self.call_duration = Histogram(
            'call_duration_seconds',
            'Call duration in seconds',
            buckets=[10, 30, 60, 120, 300, 600, 1200],
            registry=self.registry
        )
        
        # Webhook metrics
        self.webhook_deliveries = PrometheusCounter(
            'webhook_deliveries_total',
            'Total webhook delivery attempts',
            ['status'],
            registry=self.registry
        )
        
        self.webhook_delivery_time = Histogram(
            'webhook_delivery_duration_ms',
            'Webhook delivery time in milliseconds',
            buckets=[100, 500, 1000, 2000, 5000, 10000, 30000],
            registry=self.registry
        )
        
        # System metrics
        self.active_sessions = Gauge(
            'active_call_sessions',
            'Number of active call sessions',
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'outbox_queue_size',
            'Number of messages in outbox queue',
            registry=self.registry
        )
        
        self.redis_operations = PrometheusCounter(
            'redis_operations_total',
            'Total Redis operations',
            ['operation', 'status'],
            registry=self.registry
        )
    
    # Call Metrics
    
    def record_call_started(self, call_id: str, phone_hash: str) -> None:
        """Record that a call has started"""
        metrics = CallMetrics(
            call_id=call_id,
            phone_hash=phone_hash,
            started_at=datetime.now(),
            status="started"
        )
        
        self.call_metrics[call_id] = metrics
        self.calls_started.labels(status="started").inc()
        self.counters["calls_started"] += 1
        
        self._record_event("call_started", 1, {"call_id": call_id, "phone_hash": phone_hash})
        
        self.logger.info("Call started", call_id=call_id, phone_hash=phone_hash)
    
    def record_call_completed(self, call_id: str, adversarial_score: float = 0.0, 
                            fields_extracted: int = 0) -> None:
        """Record that a call has completed"""
        if call_id not in self.call_metrics:
            self.logger.warning("Call completed but no start record found", call_id=call_id)
            return
        
        metrics = self.call_metrics[call_id]
        metrics.completed_at = datetime.now()
        metrics.status = "completed"
        metrics.adversarial_score = adversarial_score
        metrics.fields_extracted = fields_extracted
        
        if metrics.started_at:
            duration = (metrics.completed_at - metrics.started_at).total_seconds()
            metrics.duration_seconds = int(duration)
            self.call_duration.observe(duration)
        
        # Categorize adversarial level
        adversarial_level = "low"
        if adversarial_score > 7:
            adversarial_level = "high"
        elif adversarial_score > 4:
            adversarial_level = "medium"
        
        self.calls_completed.labels(status="completed", adversarial_level=adversarial_level).inc()
        self.counters["calls_completed"] += 1
        
        self._record_event("call_completed", 1, {
            "call_id": call_id,
            "adversarial_score": str(adversarial_score),
            "fields_extracted": str(fields_extracted)
        })
        
        self.logger.info("Call completed", call_id=call_id, 
                        duration_seconds=metrics.duration_seconds,
                        adversarial_score=adversarial_score,
                        fields_extracted=fields_extracted)
    
    def record_call_failed(self, call_id: str, error_reason: str = "unknown") -> None:
        """Record that a call has failed"""
        if call_id in self.call_metrics:
            self.call_metrics[call_id].status = "failed"
        
        self.calls_completed.labels(status="failed", adversarial_level="unknown").inc()
        self.counters["calls_failed"] += 1
        
        self._record_event("call_failed", 1, {"call_id": call_id, "error": error_reason})
        
        self.logger.error("Call failed", call_id=call_id, error_reason=error_reason)
    
    # Webhook Metrics
    
    def record_webhook_delivery(self, call_id: str, success: bool, 
                              delivery_time_ms: int, retry_count: int = 0) -> None:
        """Record webhook delivery attempt"""
        status = "success" if success else "failed"
        
        self.webhook_deliveries.labels(status=status).inc()
        self.webhook_delivery_time.observe(delivery_time_ms)
        
        if call_id in self.call_metrics:
            self.call_metrics[call_id].webhook_delivered = success
            self.call_metrics[call_id].webhook_delivery_time_ms = delivery_time_ms
        
        self.counters[f"webhook_{status}"] += 1
        
        self._record_event("webhook_delivery", 1, {
            "call_id": call_id,
            "status": status,
            "delivery_time_ms": str(delivery_time_ms),
            "retry_count": str(retry_count)
        })
        
        self.logger.info("Webhook delivery recorded", call_id=call_id, 
                        status=status, delivery_time_ms=delivery_time_ms)
    
    # System Metrics
    
    def update_system_metrics(self) -> None:
        """Update system-level metrics from Redis"""
        try:
            # Get Redis stats
            redis_stats = self.redis_service.get_system_stats()
            
            # Update active sessions
            active_sessions = redis_stats.get("active_call_sessions", 0)
            self.active_sessions.set(active_sessions)
            
            # Update queue size
            queue_size = redis_stats.get("pending_outbox_messages", 0)
            self.queue_size.set(queue_size)
            
            self.counters["system_metrics_updated"] += 1
            
        except Exception as e:
            self.logger.error("Failed to update system metrics", error=str(e))
    
    def record_redis_operation(self, operation: str, success: bool) -> None:
        """Record Redis operation metrics"""
        status = "success" if success else "failed"
        self.redis_operations.labels(operation=operation, status=status).inc()
    
    # Event Recording
    
    def _record_event(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Record a metric event"""
        event = MetricEvent(
            name=name,
            value=value,
            labels=labels or {},
            timestamp=datetime.now()
        )
        
        self.recent_events.append(event)
    
    # Analytics and Reporting
    
    def get_call_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get call analytics for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent calls
        recent_calls = [
            metrics for metrics in self.call_metrics.values()
            if metrics.started_at >= cutoff_time
        ]
        
        if not recent_calls:
            return {
                "period_hours": hours,
                "total_calls": 0,
                "completed_calls": 0,
                "failed_calls": 0,
                "average_duration": 0,
                "adversarial_distribution": {},
                "webhook_success_rate": 0
            }
        
        # Calculate statistics
        total_calls = len(recent_calls)
        completed_calls = len([c for c in recent_calls if c.status == "completed"])
        failed_calls = len([c for c in recent_calls if c.status == "failed"])
        
        # Average duration
        durations = [c.duration_seconds for c in recent_calls if c.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Adversarial score distribution
        adversarial_scores = [c.adversarial_score for c in recent_calls if c.status == "completed"]
        adversarial_dist = {
            "low": len([s for s in adversarial_scores if s <= 4]),
            "medium": len([s for s in adversarial_scores if 4 < s <= 7]),
            "high": len([s for s in adversarial_scores if s > 7])
        }
        
        # Webhook success rate
        webhook_attempts = [c for c in recent_calls if c.status == "completed"]
        webhook_successes = len([c for c in webhook_attempts if c.webhook_delivered])
        webhook_success_rate = (webhook_successes / len(webhook_attempts) * 100) if webhook_attempts else 0
        
        return {
            "period_hours": hours,
            "total_calls": total_calls,
            "completed_calls": completed_calls,
            "failed_calls": failed_calls,
            "success_rate": (completed_calls / total_calls * 100) if total_calls > 0 else 0,
            "average_duration_seconds": int(avg_duration),
            "adversarial_distribution": adversarial_dist,
            "webhook_success_rate": round(webhook_success_rate, 1),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        # Update system metrics first
        self.update_system_metrics()
        
        # Get Redis health
        redis_health = self.redis_service.health_check()
        
        # Calculate recent error rates
        recent_events = [e for e in self.recent_events 
                        if e.timestamp >= datetime.now() - timedelta(minutes=15)]
        
        error_events = [e for e in recent_events if "failed" in e.name or "error" in e.name]
        error_rate = (len(error_events) / len(recent_events) * 100) if recent_events else 0
        
        return {
            "status": "healthy" if error_rate < 10 and redis_health["status"] == "healthy" else "unhealthy",
            "redis_health": redis_health,
            "active_sessions": int(self.active_sessions._value.get()),
            "queue_size": int(self.queue_size._value.get()),
            "error_rate_15min": round(error_rate, 2),
            "total_events_15min": len(recent_events),
            "counters": dict(self.counters),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics"""
        # Update system metrics before generating output
        self.update_system_metrics()
        return generate_latest(self.registry).decode('utf-8')
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent metric events"""
        events = list(self.recent_events)[-limit:]
        return [
            {
                "name": event.name,
                "value": event.value,
                "labels": event.labels,
                "timestamp": event.timestamp.isoformat()
            }
            for event in events
        ]
    
    def cleanup_old_metrics(self, hours: int = 48) -> int:
        """Clean up old call metrics to prevent memory bloat"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        old_calls = [
            call_id for call_id, metrics in self.call_metrics.items()
            if metrics.started_at < cutoff_time
        ]
        
        for call_id in old_calls:
            del self.call_metrics[call_id]
        
        self.logger.info("Cleaned up old metrics", removed_count=len(old_calls))
        return len(old_calls)
    
    def export_metrics_summary(self) -> Dict[str, Any]:
        """Export a comprehensive metrics summary"""
        return {
            "system_health": self.get_system_health(),
            "call_analytics_24h": self.get_call_analytics(24),
            "call_analytics_1h": self.get_call_analytics(1),
            "recent_events": self.get_recent_events(50),
            "exported_at": datetime.now().isoformat()
        }
