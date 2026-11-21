import re
import time
from typing import Dict, Any, List, Optional
from .models import Draft, SafetyAuditRecord
from .runtime import AgentRuntime
from .tools import ToolRegistry


class SafetyGovernanceAgent:
    """
    Lab 12: Safety, Governance and Human Approval Agent.
    
    Acts as an ethical and security guardrail:
    - Scans for PII leaks (passwords, phone numbers, secret tokens).
    - Detects prompt injection markers and toxic phrasing.
    - Strictly enforces Human-in-the-Loop policy: drafts remain PENDING_APPROVAL.
    - Prevents automated external transmission.
    """

    def __init__(self, tools: ToolRegistry, runtime: AgentRuntime):
        self.name = "SafetyGovernanceAgent"
        self.tools = tools
        self.runtime = runtime

        # Common PII & sensitive patterns
        self.pii_patterns = {
            "PHONE_NUMBER": r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "SECRET_OR_PASSWORD": r'(?i)\b(password|secret|apikey|token|private_key)\s*(?:[:=]|\bis\b)\s*\S+',
            "SSN_OR_GOVT_ID": r'\b\d{3}-\d{2}-\d{4}\b',
        }

        # Prompt injection markers
        self.injection_markers = [
            "ignore previous instructions",
            "system override",
            "disregard safety guidelines",
            "you are now unrestricted"
        ]

    def audit_draft(self, draft: Draft) -> SafetyAuditRecord:
        """Scan a draft for safety compliance, PII leaks, and approval status."""
        start_time = time.perf_counter()
        full_text = f"{draft.subject} {draft.body}"
        detected_pii = []

        # Check for PII
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, full_text):
                detected_pii.append(pii_type)

        # Check for injection or prompt leakage
        has_injection = any(marker in full_text.lower() for marker in self.injection_markers)

        # Strictly enforce approval status
        if draft.status != "PENDING_APPROVAL":
            # Guardrail intervention: revert status
            draft.status = "PENDING_APPROVAL"
            policy_compliance = False
            notes = "Status was modified from PENDING_APPROVAL; reverted by SafetyGovernanceAgent."
        else:
            policy_compliance = True
            notes = "Strict human approval verified: draft queued for manual review."

        risk_level = "LOW"
        if detected_pii or has_injection or not policy_compliance:
            risk_level = "HIGH"
        elif draft.to.count("@") != 1:
            risk_level = "MEDIUM"

        record = SafetyAuditRecord(
            email_id=draft.email_id,
            pii_detected=detected_pii,
            sensitive_content_flagged=has_injection or bool(detected_pii),
            policy_compliance=policy_compliance,
            human_approval_required=True,
            risk_level=risk_level,
            notes=notes
        )

        self.tools.call(
            "audit_log",
            agent_name=self.name,
            action="safety_governance_audit",
            email_id=draft.email_id,
            details={
                "risk_level": risk_level,
                "pii_detected": detected_pii,
                "policy_compliant": policy_compliance
            }
        )

        self.runtime.track(
            self.name,
            f"audit_draft_{draft.email_id}",
            start_time,
            details={"risk": risk_level}
        )
        return record

    def audit_all(self, drafts: List[Draft]) -> Dict[str, SafetyAuditRecord]:
        """Audit all drafts in the workflow."""
        audit_results = {}
        for d in drafts:
            audit_results[d.email_id] = self.audit_draft(d)
        return audit_results
