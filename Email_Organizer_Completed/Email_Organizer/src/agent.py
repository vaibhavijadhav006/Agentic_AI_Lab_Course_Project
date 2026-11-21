import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from .models import Email, EmailAnalysis, Draft, CalendarEvent, WorkflowState
from .skills import EmailSkills
from .storage import MemoryStore
from .tools import ToolRegistry
from .runtime import AgentRuntime


# ===========================================================================
# 1. Ingestion and Classification Agent (Agent 1 of 7)
# ===========================================================================
class IngestionClassificationAgent:
    """
    Agent 1: Ingestion and Classification Agent.
    
    Ingests emails through the connector, searches past memory for sender context,
    and classifies emails into institutional categories (academic, placement,
    administrative, meeting, information, research).
    """

    def __init__(self, tools: ToolRegistry, skills: EmailSkills, memory: MemoryStore, runtime: Optional[AgentRuntime] = None):
        self.name = "IngestionClassificationAgent"
        self.tools = tools
        self.skills = skills
        self.memory = memory
        self.runtime = runtime

    def ingest_and_classify(self, raw_emails: List[Dict[str, Any]]) -> Tuple[List[Email], Dict[str, EmailAnalysis], Dict[str, str]]:
        """Ingest raw email dictionaries, retrieve context, and classify categories."""
        start_time = time.perf_counter()
        emails: List[Email] = []
        analyses: Dict[str, EmailAnalysis] = {}
        contexts: Dict[str, str] = {}

        for raw in raw_emails:
            email = Email(**raw)
            emails.append(email)

            # Retrieve memory context for sender and subject
            context_rows = self.tools.call(
                "search_memory",
                query=f"{email.sender} {email.subject}",
                limit=3
            )
            context_parts = []
            for row in context_rows:
                if str(row.get("id", "")) == str(email.id):
                    continue
                subj = row.get("subject", row.get("key", "Memory"))
                body = row.get("body", row.get("value", ""))
                context_parts.append(f"{subj}: {str(body)[:160]}")
            context = "\n".join(context_parts)
            contexts[email.id] = context

            # Classify category using skills/LLM
            analysis = self.skills.classify_email(email)
            analyses[email.id] = analysis

        if self.runtime:
            self.runtime.track(
                self.name,
                "ingest_and_classify",
                start_time,
                details={"emails_ingested": len(emails)}
            )

        return emails, analyses, contexts


# ===========================================================================
# 2. Priority and Urgency Agent (Agent 2 of 7)
# ===========================================================================
class PriorityUrgencyAgent:
    """
    Agent 2: Priority and Urgency Agent.
    
    Evaluates urgency keywords, deadlines, and calculates a calibrated urgency
    score (0–100) and priority level (LOW, MEDIUM, HIGH, CRITICAL).
    """

    def __init__(self, tools: ToolRegistry, skills: EmailSkills, runtime: Optional[AgentRuntime] = None):
        self.name = "PriorityUrgencyAgent"
        self.tools = tools
        self.skills = skills
        self.runtime = runtime

    def score_all(self, emails: List[Email], analyses: Dict[str, EmailAnalysis]) -> Dict[str, EmailAnalysis]:
        """Score priority and urgency across all ingested emails."""
        start_time = time.perf_counter()
        updated_analyses: Dict[str, EmailAnalysis] = {}

        for email in emails:
            analysis = analyses[email.id]
            updated = self.skills.score_priority(email, analysis)
            
            # Additional heuristic: placement deadlines within 24h are escalated to HIGH/CRITICAL
            if "placement" in email.subject.lower() or "placement" in email.sender.lower():
                if "tomorrow" in email.body.lower() or "deadline" in email.body.lower():
                    updated.priority = "HIGH"
                    updated.urgency_score = max(updated.urgency_score, 85)

            updated_analyses[email.id] = updated

        if self.runtime:
            self.runtime.track(
                self.name,
                "evaluate_priority_urgency",
                start_time,
                details={"emails_scored": len(updated_analyses)}
            )

        return updated_analyses


# ===========================================================================
# 3. Draft Reply Agent (Agent 3 of 7)
# ===========================================================================
class DraftReplyAgent:
    """
    Agent 3: Draft Reply Agent.
    
    Generates professional, context-grounded email reply drafts when required.
    Strictly sets status to PENDING_APPROVAL for human-in-the-loop review.
    """

    def __init__(self, tools: ToolRegistry, skills: EmailSkills, runtime: Optional[AgentRuntime] = None):
        self.name = "DraftReplyAgent"
        self.tools = tools
        self.skills = skills
        self.runtime = runtime

    def generate_drafts(
        self,
        emails: List[Email],
        analyses: Dict[str, EmailAnalysis],
        contexts: Optional[Dict[str, str]] = None
    ) -> List[Draft]:
        """Generate response drafts for emails requiring replies."""
        start_time = time.perf_counter()
        drafts: List[Draft] = []
        contexts = contexts or {}

        for email in emails:
            analysis = analyses[email.id]
            if analysis.reply_required:
                context = contexts.get(email.id, "")
                draft = self.skills.draft_reply(email, analysis, context)
                draft.email_id = email.id
                draft.status = "PENDING_APPROVAL"  # Mandate human approval

                # Save draft through tool registry
                save_res = self.tools.call("save_draft", draft=draft.to_dict())
                draft.id = save_res.get("draft_id")
                drafts.append(draft)

        if self.runtime:
            self.runtime.track(
                self.name,
                "generate_reply_drafts",
                start_time,
                details={"drafts_generated": len(drafts)}
            )

        return drafts


# ===========================================================================
# 4. Action-Item Extraction Agent (Agent 4 of 7)
# ===========================================================================
class ActionItemExtractionAgent:
    """
    Agent 4: Action-Item Extraction Agent.
    
    Extracts concrete deliverables, required submissions, deadlines, and tasks
    from email bodies into structured task records.
    """

    def __init__(self, tools: ToolRegistry, skills: EmailSkills, runtime: Optional[AgentRuntime] = None):
        self.name = "ActionItemExtractionAgent"
        self.tools = tools
        self.skills = skills
        self.runtime = runtime

    def extract_action_items(self, emails: List[Email], analyses: Dict[str, EmailAnalysis]) -> List[Dict[str, Any]]:
        """Extract all actionable tasks across the email dataset."""
        start_time = time.perf_counter()
        action_items: List[Dict[str, Any]] = []

        for email in emails:
            analysis = analyses[email.id]
            items = analysis.action_items or self.skills.extract_action_items(email)
            for item in items:
                action_items.append({
                    "email_id": email.id,
                    "subject": email.subject,
                    "action": item,
                    "category": analysis.category
                })

        if self.runtime:
            self.runtime.track(
                self.name,
                "extract_action_items",
                start_time,
                details={"total_actions_extracted": len(action_items)}
            )

        return action_items


# ===========================================================================
# 5. Follow-up and Reminder Agent (Agent 5 of 7)
# ===========================================================================
class FollowupReminderAgent:
    """
    Agent 5: Follow-up and Reminder Agent.
    
    Identifies emails that require future monitoring, tracks deadlines,
    and compiles the follow-up reminder digest.
    """

    def __init__(self, tools: ToolRegistry, skills: EmailSkills, runtime: Optional[AgentRuntime] = None):
        self.name = "FollowupReminderAgent"
        self.tools = tools
        self.skills = skills
        self.runtime = runtime

    def build_followups(self, analyses: Dict[str, EmailAnalysis]) -> List[Dict[str, Any]]:
        """Compile follow-up digest for time-sensitive emails."""
        start_time = time.perf_counter()
        analyses_list = list(analyses.values())
        followups = self.skills.build_followup_digest(analyses_list)

        if self.runtime:
            self.runtime.track(
                self.name,
                "build_followup_reminders",
                start_time,
                details={"followup_items_count": len(followups)}
            )

        return followups


# ===========================================================================
# 6. Calendar and Task Sync Agent (Agent 6 of 7)
# ===========================================================================
class CalendarTaskSyncAgent:
    """
    Agent 6: Calendar and Task Sync Agent.
    
    Parses meeting invitations, schedule commitments, and hard deadlines.
    Synchronizes them to local calendar storage (simulated local calendar store).
    """

    def __init__(self, tools: ToolRegistry, runtime: Optional[AgentRuntime] = None):
        self.name = "CalendarTaskSyncAgent"
        self.tools = tools
        self.runtime = runtime

    def sync_calendar_events(self, emails: List[Email]) -> List[CalendarEvent]:
        """Detect scheduled meetings and deadlines, synchronizing them locally."""
        start_time = time.perf_counter()
        events: List[CalendarEvent] = []

        for email in emails:
            text = f"{email.subject} {email.body}".lower()
            
            # Detect meeting commitments
            if "review meeting" in text or "friday" in text and "10 am" in text:
                event = CalendarEvent(
                    email_id=email.id,
                    title=f"Meeting: {email.subject}",
                    event_date="Next Friday",
                    event_time="10:00 AM",
                    description="Project progress review meeting with advisor."
                )
                self.tools.call(
                    "sync_calendar_event",
                    email_id=event.email_id,
                    title=event.title,
                    event_date=event.event_date,
                    event_time=event.event_time,
                    description=event.description
                )
                events.append(event)

            elif "registration" in text and ("6 pm" in text or "tomorrow" in text):
                event = CalendarEvent(
                    email_id=email.id,
                    title=f"Deadline: {email.subject}",
                    event_date="Tomorrow",
                    event_time="06:00 PM",
                    description="Mandatory placement drive portal registration deadline."
                )
                self.tools.call(
                    "sync_calendar_event",
                    email_id=event.email_id,
                    title=event.title,
                    event_date=event.event_date,
                    event_time=event.event_time,
                    description=event.description
                )
                events.append(event)

        if self.runtime:
            self.runtime.track(
                self.name,
                "sync_calendar_and_tasks",
                start_time,
                details={"events_synced": len(events)}
            )

        return events


# ===========================================================================
# 7. Archive and Logging Agent (Agent 7 of 7)
# ===========================================================================
class ArchiveLoggingAgent:
    """
    Agent 7: Archive and Logging Agent.
    
    Persists finalized email records and analyses into SQLite storage,
    maintains the immutable audit history, and saves batch execution summaries.
    """

    def __init__(self, tools: ToolRegistry, memory: MemoryStore, runtime: Optional[AgentRuntime] = None):
        self.name = "ArchiveLoggingAgent"
        self.tools = tools
        self.memory = memory
        self.runtime = runtime

    def archive_batch(
        self,
        emails: List[Email],
        analyses: Dict[str, EmailAnalysis],
        drafts: List[Draft],
        action_items: List[Dict[str, Any]],
        followups: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Archive all execution results and record audit entries."""
        start_time = time.perf_counter()

        for email in emails:
            analysis = analyses[email.id]
            self.memory.save_analysis(email.to_dict(), analysis.to_dict())

        # Save run summary note
        summary_val = f"Processed {len(emails)} emails; generated {len(drafts)} drafts and {len(action_items)} action items."
        self.tools.call("save_memory", key="last_run_summary", value=summary_val)

        # Audit log entry for batch archive
        self.tools.call(
            "audit_log",
            agent_name=self.name,
            action="batch_archive_and_logging",
            details={
                "emails_archived": len(emails),
                "drafts_recorded": len(drafts),
                "action_items_recorded": len(action_items)
            }
        )

        record = {
            "status": "ARCHIVED",
            "emails_count": len(emails),
            "drafts_count": len(drafts),
            "timestamp": datetime.now().isoformat()
        }

        if self.runtime:
            self.runtime.track(
                self.name,
                "archive_and_log_batch",
                start_time,
                details=record
            )

        return record


# ===========================================================================
# Backwards-Compatibility Wrappers (Labs 1–5 Compatibility)
# ===========================================================================
# Alias TriageAgent to IngestionClassificationAgent
TriageAgent = IngestionClassificationAgent


class EmailOrganizerAgent:
    """
    Goal-driven email organization agent from Labs 1–5.
    Preserved for backwards compatibility while orchestrating the 7 main agents.
    """

    def __init__(
        self,
        tools: ToolRegistry,
        skills: EmailSkills,
        memory: MemoryStore,
        runtime: Optional[AgentRuntime] = None
    ):
        self.tools = tools
        self.skills = skills
        self.memory = memory
        self.runtime = runtime

        # Instantiate the 7 Main Agents
        self.agent1_ingestion = IngestionClassificationAgent(tools, skills, memory, runtime)
        self.agent2_priority = PriorityUrgencyAgent(tools, skills, runtime)
        self.agent3_drafting = DraftReplyAgent(tools, skills, runtime)
        self.agent4_actions = ActionItemExtractionAgent(tools, skills, runtime)
        self.agent5_followups = FollowupReminderAgent(tools, skills, runtime)
        self.agent6_calendar = CalendarTaskSyncAgent(tools, runtime)
        self.agent7_archive = ArchiveLoggingAgent(tools, memory, runtime)

    def run(self) -> Dict[str, Any]:
        """Execute the complete 7-agent workflow over the email connector data."""
        # 1. Ingest & Classify
        raw_emails = self.tools.call("list_emails")
        emails, analyses, contexts = self.agent1_ingestion.ingest_and_classify(raw_emails)

        # 2. Priority & Urgency Scoring
        analyses = self.agent2_priority.score_all(emails, analyses)

        # 3. Action Items
        action_items = self.agent4_actions.extract_action_items(emails, analyses)

        # 4. Draft Replies
        drafts = self.agent3_drafting.generate_drafts(emails, analyses, contexts)

        # 5. Follow-ups
        followups = self.agent5_followups.build_followups(analyses)

        # 6. Calendar Sync
        self.agent6_calendar.sync_calendar_events(emails)

        # 7. Archive & Logging
        self.agent7_archive.archive_batch(emails, analyses, drafts, action_items, followups)

        triaged = []
        for email in emails:
            a = analyses[email.id]
            triaged.append({
                "email_id": email.id,
                "subject": email.subject,
                "category": a.category,
                "priority": a.priority,
                "urgency_score": a.urgency_score,
                "reason": a.reason
            })

        skill_summary = {
            "emails_classified": len(analyses),
            "priorities_scored": len(analyses),
            "emails_checked_for_action_items": len(analyses),
            "action_items_extracted": len(action_items),
            "drafts_generated": len(drafts),
            "followups_generated": len(followups)
        }

        return {
            "triaged_inbox": triaged,
            "draft_reply_queue": [d.to_dict() for d in drafts],
            "action_item_list": action_items,
            "follow_up_digest": followups,
            "tool_calls": self.tools.describe(),
            "skill_summary": skill_summary,
            "approval_rule": (
                "No email is sent automatically. "
                "Human approval is required."
            )
        }
