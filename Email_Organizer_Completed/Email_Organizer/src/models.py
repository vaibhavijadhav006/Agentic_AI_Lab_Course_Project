from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class Email:
    id: str
    sender: str
    subject: str
    body: str
    received_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EmailAnalysis:
    email_id: str
    category: str
    priority: str
    urgency_score: int
    action_items: List[str] = field(default_factory=list)
    follow_up_date: Optional[str] = None
    reply_required: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Draft:
    email_id: str
    to: str
    subject: str
    body: str
    status: str = "PENDING_APPROVAL"
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CalendarEvent:
    """Represents a scheduled calendar entry or deadline task."""
    email_id: str
    title: str
    event_date: str
    event_time: str
    description: str
    status: str = "SCHEDULED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentExecutionRecord:
    """Lab 6: Execution logging and monitoring telemetry."""
    agent_name: str
    action: str
    status: str
    latency_ms: float
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchDossier:
    """Lab 9: Deep research agent contextual inquiry result."""
    email_id: str
    topic: str
    query_expanded: List[str]
    findings: str
    citations: List[str]
    confidence_score: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DisciplineRecommendation:
    """Lab 13: Discipline-specific specialist agent recommendations."""
    email_id: str
    discipline: str  # academic | placement | administrative | research
    agent_name: str
    recommendations: List[str]
    suggested_reply: Optional[str] = None
    priority_override: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyAuditRecord:
    """Lab 12: Safety, governance and human-in-the-loop audit record."""
    email_id: str
    pii_detected: List[str]
    sensitive_content_flagged: bool
    policy_compliance: bool
    human_approval_required: bool
    risk_level: str  # LOW | MEDIUM | HIGH
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QATestResult:
    """Lab 11: Agentic SDLC factory verification and test outcome."""
    test_id: str
    test_name: str
    category: str
    passed: bool
    message: str
    duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowState:
    """Shared state passed through the agentic node graph."""
    emails: List[Email] = field(default_factory=list)
    analyses: Dict[str, EmailAnalysis] = field(default_factory=dict)
    research_dossiers: Dict[str, ResearchDossier] = field(default_factory=dict)
    discipline_recommendations: Dict[str, List[DisciplineRecommendation]] = field(default_factory=dict)
    drafts: List[Draft] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    followups: List[Dict[str, Any]] = field(default_factory=list)
    calendar_events: List[CalendarEvent] = field(default_factory=list)
    safety_records: Dict[str, SafetyAuditRecord] = field(default_factory=dict)
    qa_results: List[QATestResult] = field(default_factory=list)
    execution_trace: List[AgentExecutionRecord] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emails_count": len(self.emails),
            "analyses": {k: v.to_dict() for k, v in self.analyses.items()},
            "research_dossiers": {k: v.to_dict() for k, v in self.research_dossiers.items()},
            "discipline_recommendations": {
                k: [rec.to_dict() for rec in v] for k, v in self.discipline_recommendations.items()
            },
            "drafts": [d.to_dict() for d in self.drafts],
            "action_items": self.action_items,
            "followups": self.followups,
            "calendar_events": [c.to_dict() for c in self.calendar_events],
            "safety_records": {k: v.to_dict() for k, v in self.safety_records.items()},
            "qa_results": [r.to_dict() for r in self.qa_results],
            "execution_trace_count": len(self.execution_trace),
            "metrics": self.metrics,
        }
