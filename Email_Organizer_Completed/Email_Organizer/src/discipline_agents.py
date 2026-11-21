import time
from typing import Dict, Any, List, Optional
from .models import Email, EmailAnalysis, Draft, DisciplineRecommendation, ResearchDossier
from .runtime import AgentRuntime
from .tools import ToolRegistry


class AcademicAdvisorAgent:
    """
    Lab 13: Discipline-Specific Agent for Academic Affairs.
    
    Specializes in coursework, research submissions, project milestones,
    and professor correspondence.
    """

    def __init__(self, tools: ToolRegistry, runtime: AgentRuntime):
        self.name = "AcademicAdvisorAgent"
        self.discipline = "academic"
        self.tools = tools
        self.runtime = runtime

    def process(
        self,
        email: Email,
        analysis: EmailAnalysis,
        dossier: Optional[ResearchDossier] = None
    ) -> Optional[DisciplineRecommendation]:
        if analysis.category != "academic" and "prof" not in email.sender and "assignment" not in email.subject.lower():
            return None

        start_time = time.perf_counter()
        recs = []
        suggested_reply = None

        if "assignment" in email.subject.lower() or "bfs" in email.body.lower():
            recs.append("Verify CS301 graph traversal requirements (BFS for shortest path, DFS for topological sort).")
            recs.append("Prepare clear algorithmic explanation with time/space complexity notes for professor.")
            suggested_reply = (
                f"Dear Professor,\n\n"
                f"Thank you for reaching out regarding the assignment. In accordance with the course specification, "
                f"the graph traversal implementation utilizes Breadth-First Search (BFS) for shortest path routing "
                f"and Depth-First Search (DFS) for cycle detection. I have documented both in the report comments.\n\n"
                f"Respectfully,\nStudent"
            )
        elif "review" in email.subject.lower() or "progress" in email.body.lower():
            recs.append("Prepare two-page project milestone summary per college guidelines.")
            recs.append("Assemble slide deck for Friday 10 AM review meeting with sprint deliverables.")
            suggested_reply = (
                f"Dear Professor,\n\n"
                f"Thank you for the notification. I am completing the milestone report and will submit the PDF "
                f"well before Friday 5 PM. I will be ready for our review session at 10 AM.\n\n"
                f"Respectfully,\nStudent"
            )
        elif "paper" in email.subject.lower() or "research" in email.subject.lower():
            recs.append("Review cited papers for literature review section.")
            recs.append("Prepare 1-page comparative summary for next advisory meeting.")
            suggested_reply = (
                f"Dear Professor,\n\n"
                f"Thank you for sharing these research papers. I will review the methodologies and incorporate "
                f"relevant insights into the literature review section.\n\n"
                f"Respectfully,\nStudent"
            )
        else:
            recs.append(f"Review academic notice from {email.sender}.")
            suggested_reply = (
                f"Dear Professor,\n\n"
                f"Thank you for your email. I have noted the details regarding '{email.subject}' and will comply.\n\n"
                f"Respectfully,\nStudent"
            )

        recommendation = DisciplineRecommendation(
            email_id=email.id,
            discipline=self.discipline,
            agent_name=self.name,
            recommendations=recs,
            suggested_reply=suggested_reply,
            priority_override=analysis.priority
        )

        self.tools.call(
            "audit_log",
            agent_name=self.name,
            action="academic_discipline_evaluation",
            email_id=email.id,
            details={"recommendations_count": len(recs)}
        )

        self.runtime.track(self.name, f"evaluate_{email.id}", start_time)
        return recommendation


class PlacementSpecialistAgent:
    """
    Lab 13: Discipline-Specific Agent for Career & Placement Cell.
    
    Specializes in corporate drive registrations, resume screening,
    recruiter deadlines, and student interview preparation.
    """

    def __init__(self, tools: ToolRegistry, runtime: AgentRuntime):
        self.name = "PlacementSpecialistAgent"
        self.discipline = "placement"
        self.tools = tools
        self.runtime = runtime

    def process(
        self,
        email: Email,
        analysis: EmailAnalysis,
        dossier: Optional[ResearchDossier] = None
    ) -> Optional[DisciplineRecommendation]:
        if analysis.category != "placement" and "placement" not in email.sender and "registration" not in email.subject.lower():
            return None

        start_time = time.perf_counter()
        recs = [
            "Check placement portal credentials and verify all mandatory resume fields.",
            "Complete mandatory drive registration before deadline tomorrow 6 PM to prevent de-listing.",
            "Verify all semester transcripts are uploaded and attested in profile."
        ]

        suggested_reply = (
            f"Dear Placement Team,\n\n"
            f"Thank you for the notification regarding '{email.subject}'. I have accessed the portal, "
            f"completed the placement registration, and verified all profile details.\n\n"
            f"Best regards,\nStudent (Roll No: CS-2024-042)"
        )

        recommendation = DisciplineRecommendation(
            email_id=email.id,
            discipline=self.discipline,
            agent_name=self.name,
            recommendations=recs,
            suggested_reply=suggested_reply,
            priority_override="HIGH"  # Placement deadlines always treated with high priority
        )

        self.tools.call(
            "audit_log",
            agent_name=self.name,
            action="placement_discipline_evaluation",
            email_id=email.id,
            details={"priority": "HIGH", "deadline": "tomorrow 6 PM"}
        )

        self.runtime.track(self.name, f"evaluate_{email.id}", start_time)
        return recommendation


class AdministrativeOfficerAgent:
    """
    Lab 13: Discipline-Specific Agent for Departmental Administration.
    
    Specializes in departmental minutes, regulatory notices, faculty meetings,
    and administrative compliance.
    """

    def __init__(self, tools: ToolRegistry, runtime: AgentRuntime):
        self.name = "AdministrativeOfficerAgent"
        self.discipline = "administrative"
        self.tools = tools
        self.runtime = runtime

    def process(
        self,
        email: Email,
        analysis: EmailAnalysis,
        dossier: Optional[ResearchDossier] = None
    ) -> Optional[DisciplineRecommendation]:
        if analysis.category not in ["administrative", "meeting"] and "hod" not in email.sender:
            return None

        start_time = time.perf_counter()
        recs = [
            "Archive department minutes in institutional compliance repository.",
            "Check for student representation agenda items in next quarterly review.",
            "Acknowledge receipt within standard 3-day departmental window."
        ]

        suggested_reply = (
            f"Dear Department Office / HOD,\n\n"
            f"Thank you for sharing the '{email.subject}'. The minutes have been received, reviewed, "
            f"and recorded for reference.\n\n"
            f"Sincerely,\nStudent Representative"
        )

        recommendation = DisciplineRecommendation(
            email_id=email.id,
            discipline=self.discipline,
            agent_name=self.name,
            recommendations=recs,
            suggested_reply=suggested_reply,
            priority_override=analysis.priority
        )

        self.tools.call(
            "audit_log",
            agent_name=self.name,
            action="admin_discipline_evaluation",
            email_id=email.id,
            details={"recommendations_count": len(recs)}
        )

        self.runtime.track(self.name, f"evaluate_{email.id}", start_time)
        return recommendation
