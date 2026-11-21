import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from .models import AgentExecutionRecord


class AgentRuntime:
    """
    Lab 6: Agent Runtime, Execution Logging and Monitoring.
    
    Provides telemetry tracking, lifecycle monitoring, latency accounting,
    and structured logging across all agent executions.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.base_dir = log_dir or (Path(__file__).resolve().parent.parent / "data")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.base_dir / "runtime_execution.log"

        # Setup dedicated logger
        self.logger = logging.getLogger("AgentRuntime")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.execution_records: List[AgentExecutionRecord] = []
        self.start_timestamp = time.time()
        self.invocations_by_agent: Dict[str, int] = {}
        self.latency_by_agent: Dict[str, float] = {}

    def log_event(self, level: str, message: str, agent: Optional[str] = None):
        agent_prefix = f"[{agent}] " if agent else ""
        full_msg = f"{agent_prefix}{message}"
        if level.upper() == "DEBUG":
            self.logger.debug(full_msg)
        elif level.upper() == "WARNING":
            self.logger.warning(full_msg)
        elif level.upper() == "ERROR":
            self.logger.error(full_msg)
        else:
            self.logger.info(full_msg)

    def track(
        self,
        agent_name: str,
        action: str,
        start_time: float,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None
    ) -> AgentExecutionRecord:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        now_iso = datetime.now().isoformat()
        
        record = AgentExecutionRecord(
            agent_name=agent_name,
            action=action,
            status=status,
            latency_ms=round(latency_ms, 2),
            timestamp=now_iso,
            details=details or {}
        )
        self.execution_records.append(record)

        # Update metrics
        self.invocations_by_agent[agent_name] = self.invocations_by_agent.get(agent_name, 0) + 1
        self.latency_by_agent[agent_name] = self.latency_by_agent.get(agent_name, 0.0) + latency_ms

        self.log_event(
            "INFO",
            f"Action '{action}' completed in {latency_ms:.2f}ms (Status: {status})",
            agent=agent_name
        )
        return record

    def get_monitoring_metrics(self) -> Dict[str, Any]:
        total_duration = time.time() - self.start_timestamp
        total_invocations = len(self.execution_records)
        avg_latency = (
            sum(r.latency_ms for r in self.execution_records) / total_invocations
            if total_invocations > 0 else 0.0
        )
        
        return {
            "uptime_seconds": round(total_duration, 2),
            "total_agent_invocations": total_invocations,
            "average_latency_ms": round(avg_latency, 2),
            "invocations_by_agent": self.invocations_by_agent,
            "cumulative_latency_by_agent_ms": {
                k: round(v, 2) for k, v in self.latency_by_agent.items()
            },
            "total_logged_events": len(self.execution_records),
            "log_file": str(self.log_file)
        }
