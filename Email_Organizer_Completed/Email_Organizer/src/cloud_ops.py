import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from .runtime import AgentRuntime


class CircuitBreaker:
    """
    Production-grade circuit breaker pattern for external / connector calls.
    States: CLOSED (normal), OPEN (tripped after failures), HALF_OPEN (probing).
    """

    def __init__(self, failure_threshold: int = 3, recovery_time_sec: float = 5.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0.0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_failure_time > self.recovery_time_sec:
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("CircuitBreaker is OPEN: external request rejected to prevent cascading failure.")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = now
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            raise e


class CloudOpsMonitor:
    """
    Lab 10: Cloud Operations, Resilience and Error Monitoring.
    
    Provides simulated cloud-native operational telemetry, circuit breaker resilience,
    health checks, and SLA tracking for college review.
    
    NOTE: Operates in simulated local cloud environment; does not require external
    cloud provider credentials.
    """

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.environment = "Simulated Local Cloud Environment (College Lab Runtime)"
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            "connector": CircuitBreaker(failure_threshold=3, recovery_time_sec=2.0),
            "storage": CircuitBreaker(failure_threshold=2, recovery_time_sec=2.0)
        }
        self.incidents: List[Dict[str, Any]] = []

    def perform_health_checks(self, storage_connected: bool, data_file_exists: bool) -> Dict[str, Any]:
        """Perform comprehensive system readiness checks."""
        db_status = "HEALTHY" if storage_connected else "DEGRADED"
        fs_status = "HEALTHY" if data_file_exists else "ERROR"
        overall = "HEALTHY" if (storage_connected and data_file_exists) else "UNHEALTHY"

        checks = {
            "environment": self.environment,
            "overall_status": overall,
            "subsystems": {
                "sqlite_memory_store": db_status,
                "email_connector_source": fs_status,
                "circuit_breaker_status": {k: cb.state for k, cb in self.circuit_breakers.items()},
                "runtime_logging": "HEALTHY"
            },
            "sla_targets": {
                "max_p95_latency_ms": 500,
                "target_availability": "99.9%",
                "zero_unauthorized_sends": "ENFORCED"
            },
            "timestamp": datetime.now().isoformat()
        }

        self.runtime.log_event("INFO", f"CloudOps Health Check: {overall}", agent="CloudOpsMonitor")
        return checks

    def record_incident(self, severity: str, message: str, subsystem: str):
        incident = {
            "incident_id": f"INC-{len(self.incidents) + 1:03d}",
            "severity": severity,
            "message": message,
            "subsystem": subsystem,
            "timestamp": datetime.now().isoformat()
        }
        self.incidents.append(incident)
        self.runtime.log_event("WARNING", f"Cloud incident logged: {incident['incident_id']} - {message}", agent="CloudOpsMonitor")
        return incident

    def get_summary(self) -> Dict[str, Any]:
        return {
            "environment": self.environment,
            "circuit_breakers": {k: cb.state for k, cb in self.circuit_breakers.items()},
            "active_incidents_count": len(self.incidents),
            "incidents": self.incidents
        }
