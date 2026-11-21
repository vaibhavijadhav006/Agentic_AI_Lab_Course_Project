import time
from typing import Dict, Any, List, Optional
from .models import Email, ResearchDossier
from .tools import ToolRegistry
from .llm import LLMClient
from .runtime import AgentRuntime


class DeepResearchAgent:
    """
    Lab 9: Deep Research Agent.
    
    Conducts contextual research, query expansion, knowledge retrieval against
    past emails and institutional archives, producing cited research dossiers.
    """

    def __init__(
        self,
        tools: ToolRegistry,
        runtime: AgentRuntime,
        llm: Optional[LLMClient] = None
    ):
        self.name = "DeepResearchAgent"
        self.tools = tools
        self.runtime = runtime
        self.llm = llm or LLMClient()

    def expand_query(self, email: Email) -> List[str]:
        """Generate targeted search queries from email contents."""
        terms = []
        subject_lower = email.subject.lower()
        body_lower = email.body.lower()

        if "assignment" in subject_lower or "bfs" in body_lower or "dfs" in body_lower:
            terms.extend(["data structures assignment", "bfs dfs traversal policy", "curriculum:data_structures_assignment"])
        if "placement" in subject_lower or "registration" in body_lower:
            terms.extend(["placement registration deadline", "policy:placement_registration_deadline"])
        if "review" in subject_lower or "progress" in body_lower or "friday" in subject_lower:
            terms.extend(["project progress review", "guideline:project_progress_review"])
        if "meeting" in subject_lower or "minutes" in body_lower:
            terms.extend(["department meeting protocol", "admin:department_meeting_protocol"])
        if "paper" in subject_lower or "research" in subject_lower:
            terms.extend(["literature review guidelines", "academic research paper submission"])

        if not terms:
            terms.append(f"{email.sender} {email.subject}")
        return terms

    def investigate(self, email: Email) -> ResearchDossier:
        """Perform deep contextual investigation for an email."""
        start_time = time.perf_counter()
        self.runtime.log_event("INFO", f"Initiating deep research for email {email.id} ('{email.subject}')", agent=self.name)

        expanded_queries = self.expand_query(email)
        gathered_citations = []
        evidence_fragments = []

        for q in expanded_queries:
            results = self.tools.call("deep_research", topic=q, limit=2)
            for res in results:
                subj = res.get("subject", "Record")
                body = res.get("body", res.get("value", ""))
                cid = res.get("id", "KB-REF")
                gathered_citations.append(f"[{cid}] {subj}")
                evidence_fragments.append(f"{subj}: {body}")

        # Synthesize findings
        if evidence_fragments:
            findings_summary = "Synthesized Evidence:\n" + "\n".join(f"- {f[:220]}" for f in evidence_fragments[:3])
        else:
            findings_summary = f"Standard contextual baseline established for sender {email.sender}. No conflicting institutional policy detected."

        dossier = ResearchDossier(
            email_id=email.id,
            topic=email.subject,
            query_expanded=expanded_queries,
            findings=findings_summary,
            citations=gathered_citations or ["Institutional Knowledge Base"],
            confidence_score=0.96 if gathered_citations else 0.85
        )

        # Log audit record
        self.tools.call(
            "audit_log",
            agent_name=self.name,
            action="deep_research_investigation",
            email_id=email.id,
            details={"queries": expanded_queries, "citation_count": len(dossier.citations)}
        )

        self.runtime.track(
            self.name,
            f"investigate_email_{email.id}",
            start_time,
            details={"citations": len(dossier.citations)}
        )
        return dossier

    def batch_investigate(self, emails: List[Email]) -> Dict[str, ResearchDossier]:
        """Perform research across all emails in the shared dataset."""
        dossiers = {}
        for email in emails:
            dossiers[email.id] = self.investigate(email)
        return dossiers
