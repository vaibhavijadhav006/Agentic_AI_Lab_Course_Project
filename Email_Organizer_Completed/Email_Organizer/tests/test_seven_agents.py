import unittest
from pathlib import Path
from src.models import Email, EmailAnalysis, WorkflowState
from src.storage import MemoryStore
from src.connectors.json_connector import JSONEmailConnector
from src.connectors.mcp_style_adapter import MCPStyleEmailAdapter
from src.skills import EmailSkills
from src.tools import ToolRegistry
from src.runtime import AgentRuntime
from src.agent import (
    IngestionClassificationAgent,
    PriorityUrgencyAgent,
    DraftReplyAgent,
    ActionItemExtractionAgent,
    FollowupReminderAgent,
    CalendarTaskSyncAgent,
    ArchiveLoggingAgent
)


class TestSevenMainAgents(unittest.TestCase):
    """Test suite verifying all Seven Main Agents perform substantive tasks on shared data."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.data_dir = cls.base_dir / "data"
        cls.memory = MemoryStore(cls.data_dir / "test_agents_memory.db")
        cls.raw_connector = JSONEmailConnector(cls.data_dir / "emails.json")
        cls.connector = MCPStyleEmailAdapter(cls.raw_connector)
        cls.skills = EmailSkills()
        cls.tools = ToolRegistry(cls.connector, cls.memory)
        cls.runtime = AgentRuntime(cls.data_dir)

        # Instantiate 7 Agents
        cls.agent1 = IngestionClassificationAgent(cls.tools, cls.skills, cls.memory, cls.runtime)
        cls.agent2 = PriorityUrgencyAgent(cls.tools, cls.skills, cls.runtime)
        cls.agent3 = DraftReplyAgent(cls.tools, cls.skills, cls.runtime)
        cls.agent4 = ActionItemExtractionAgent(cls.tools, cls.skills, cls.runtime)
        cls.agent5 = FollowupReminderAgent(cls.tools, cls.skills, cls.runtime)
        cls.agent6 = CalendarTaskSyncAgent(cls.tools, cls.runtime)
        cls.agent7 = ArchiveLoggingAgent(cls.tools, cls.memory, cls.runtime)

    @classmethod
    def tearDownClass(cls):
        cls.memory.close()
        test_db = cls.data_dir / "test_agents_memory.db"
        if test_db.exists():
            try:
                test_db.unlink()
            except Exception:
                pass

    def test_agent1_ingestion_and_classification(self):
        """Verify Agent 1 ingests emails and classifies domain categories."""
        raw = self.tools.call("list_emails")
        emails, analyses, contexts = self.agent1.ingest_and_classify(raw)
        self.assertEqual(len(emails), len(raw))
        self.assertEqual(len(analyses), len(raw))
        for eid, analysis in analyses.items():
            self.assertIn(analysis.category, ["academic", "placement", "administrative", "meeting", "information"])

    def test_agent2_priority_and_urgency(self):
        """Verify Agent 2 computes calibrated urgency score (0-100) and priority level."""
        raw = self.tools.call("list_emails")
        emails, analyses, _ = self.agent1.ingest_and_classify(raw)
        scored = self.agent2.score_all(emails, analyses)
        for eid, item in scored.items():
            self.assertTrue(0 <= item.urgency_score <= 100)
            self.assertIn(item.priority, ["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_agent3_draft_reply_pending_approval(self):
        """Verify Agent 3 generates response drafts and enforces status='PENDING_APPROVAL'."""
        raw = self.tools.call("list_emails")
        emails, analyses, contexts = self.agent1.ingest_and_classify(raw)
        scored = self.agent2.score_all(emails, analyses)
        drafts = self.agent3.generate_drafts(emails, scored, contexts)
        self.assertGreater(len(drafts), 0)
        for d in drafts:
            self.assertEqual(d.status, "PENDING_APPROVAL")
            self.assertTrue(d.subject.startswith("Re: "))
            self.assertGreater(len(d.body.strip()), 10)

    def test_agent4_action_item_extraction(self):
        """Verify Agent 4 isolates actionable tasks across email bodies."""
        raw = self.tools.call("list_emails")
        emails, analyses, _ = self.agent1.ingest_and_classify(raw)
        scored = self.agent2.score_all(emails, analyses)
        actions = self.agent4.extract_action_items(emails, scored)
        self.assertGreater(len(actions), 0)
        for act in actions:
            self.assertIn("email_id", act)
            self.assertIn("action", act)

    def test_agent5_followup_reminder(self):
        """Verify Agent 5 tracks deadline-bound emails and compiles follow-up digest."""
        raw = self.tools.call("list_emails")
        emails, analyses, _ = self.agent1.ingest_and_classify(raw)
        scored = self.agent2.score_all(emails, analyses)
        followups = self.agent5.build_followups(scored)
        self.assertGreater(len(followups), 0)
        for f in followups:
            self.assertIn("email_id", f)
            self.assertIn("priority", f)

    def test_agent6_calendar_and_task_sync(self):
        """Verify Agent 6 detects meetings and synchronizes calendar events locally."""
        raw = self.tools.call("list_emails")
        emails = [Email(**e) for e in raw]
        events = self.agent6.sync_calendar_events(emails)
        self.assertGreater(len(events), 0)
        for ev in events:
            self.assertIn("Meeting", ev.title) if "review" in ev.description.lower() else self.assertIsNotNone(ev.title)
            self.assertEqual(ev.status, "SCHEDULED")

    def test_agent7_archive_and_logging(self):
        """Verify Agent 7 records execution audit entries and saves batch status."""
        raw = self.tools.call("list_emails")
        emails, analyses, contexts = self.agent1.ingest_and_classify(raw)
        scored = self.agent2.score_all(emails, analyses)
        drafts = self.agent3.generate_drafts(emails, scored, contexts)
        actions = self.agent4.extract_action_items(emails, scored)
        followups = self.agent5.build_followups(scored)

        res = self.agent7.archive_batch(emails, scored, drafts, actions, followups)
        self.assertEqual(res["status"], "ARCHIVED")
        self.assertEqual(res["emails_count"], len(emails))


if __name__ == "__main__":
    unittest.main()
