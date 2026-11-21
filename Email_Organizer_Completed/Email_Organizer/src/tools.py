import time
from datetime import datetime
from typing import Callable, Dict, Any, List, Optional
from .storage import MemoryStore


class ToolRegistry:
    """Central registry for email, memory, research, calendar, and governance tools."""

    def __init__(self, connector, memory: MemoryStore):
        self.connector = connector
        self.memory = memory
        self.call_history: List[Dict[str, Any]] = []

        self.tools: Dict[str, Callable] = {
            "list_emails": self.connector.list_emails,
            "get_email": self.connector.get_email,
            "save_draft": self._save_draft,
            "search_memory": self._search_memory,
            "save_memory": self._save_memory,
            "deep_research": self._deep_research,
            "audit_log": self._audit_log,
            "sync_calendar_event": self._sync_calendar_event
        }

    def call(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        start_time = time.perf_counter()
        if name in ["list_emails", "search_memory", "save_draft", "save_memory", "get_email", "sync_calendar_event"]:
            print(f"\n[TOOL EXECUTED] {name}")

        try:
            result = self.tools[name](**kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            
            self.call_history.append({
                "tool": name,
                "timestamp": datetime.now().isoformat(),
                "duration_ms": round(duration_ms, 2),
                "status": "SUCCESS",
                "args_keys": list(kwargs.keys())
            })
            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.call_history.append({
                "tool": name,
                "timestamp": datetime.now().isoformat(),
                "duration_ms": round(duration_ms, 2),
                "status": "ERROR",
                "error": str(e)
            })
            raise

    def describe(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_emails",
                "description": "List emails from the connector."
            },
            {
                "name": "get_email",
                "description": "Retrieve an email using its ID."
            },
            {
                "name": "save_draft",
                "description": "Save a reply draft for human approval."
            },
            {
                "name": "search_memory",
                "description": "Search emails and saved memory notes."
            },
            {
                "name": "save_memory",
                "description": "Store a persistent memory note."
            },
            {
                "name": "deep_research",
                "description": "Execute structured knowledge search across institutional archives."
            },
            {
                "name": "audit_log",
                "description": "Record an immutable governance and execution event."
            },
            {
                "name": "sync_calendar_event",
                "description": "Synchronize a scheduled task or deadline into local calendar storage."
            }
        ]

    def _save_draft(self, draft: dict):
        res = self.memory.save_draft(draft)
        return {
            "status": "saved",
            "approval_required": True,
            "draft_id": res.get("draft_id"),
            "email_id": draft["email_id"]
        }

    def _search_memory(
        self,
        query: str,
        limit: int = 5
    ):
        return self.memory.search(
            query,
            limit=limit
        )

    def _save_memory(self, key: str, value: str):
        return self.memory.save_memory(
            key,
            value
        )

    def _deep_research(self, topic: str, limit: int = 5):
        """Query memory store specifically for institutional knowledge or policies."""
        return self.memory.search(topic, limit=limit)

    def _audit_log(self, agent_name: str, action: str, email_id: Optional[str] = None, details: Optional[dict] = None):
        self.memory.save_audit_entry(
            agent_name=agent_name,
            action=action,
            email_id=email_id,
            status="RECORDED",
            details=details or {}
        )
        return {"status": "audit_recorded", "agent": agent_name, "action": action}

    def _sync_calendar_event(self, email_id: str, title: str, event_date: str, event_time: str, description: str):
        return self.memory.save_calendar_event(
            email_id=email_id,
            title=title,
            event_date=event_date,
            event_time=event_time,
            description=description
        )

    def get_call_history(self) -> List[Dict[str, Any]]:
        return self.call_history
