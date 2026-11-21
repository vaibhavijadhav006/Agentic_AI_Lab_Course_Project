import unittest
from pathlib import Path
from src.models import Email, EmailAnalysis, Draft
from src.connectors.json_connector import JSONEmailConnector
from src.connectors.mcp_style_adapter import MCPStyleEmailAdapter
from src.skills import EmailSkills
from src.storage import MemoryStore
from src.tools import ToolRegistry
from src.agent import EmailOrganizerAgent


class TestLabs1To5(unittest.TestCase):
    """Test suite verifying existing Labs 1 to 5 functionality is intact."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.data_dir = cls.base_dir / "data"
        cls.email_file = cls.data_dir / "emails.json"
        cls.memory = MemoryStore(cls.data_dir / "test_memory.db")
        cls.raw_connector = JSONEmailConnector(cls.email_file)
        cls.email_connector = MCPStyleEmailAdapter(cls.raw_connector)
        cls.skills = EmailSkills()
        cls.tools = ToolRegistry(cls.email_connector, cls.memory)

    @classmethod
    def tearDownClass(cls):
        cls.memory.close()
        test_db = cls.data_dir / "test_memory.db"
        if test_db.exists():
            try:
                test_db.unlink()
            except Exception:
                pass

    def test_lab1_agent_vs_chatbot_loop(self):
        """Lab 1: Verify goal-driven observe-plan-act loop produces structured evidence."""
        agent = EmailOrganizerAgent(self.tools, self.skills, self.memory)
        res = agent.run()
        self.assertIn("triaged_inbox", res)
        self.assertIn("draft_reply_queue", res)
        self.assertIn("action_item_list", res)
        self.assertIn("follow_up_digest", res)
        self.assertGreater(len(res["triaged_inbox"]), 0)

    def test_lab2_tool_execution(self):
        """Lab 2: Verify tool registry executes tools dynamically."""
        emails = self.tools.call("list_emails")
        self.assertIsInstance(emails, list)
        self.assertGreater(len(emails), 0)

        first_id = emails[0]["id"]
        email = self.tools.call("get_email", email_id=first_id)
        self.assertEqual(email["id"], first_id)

    def test_lab3_skills(self):
        """Lab 3: Verify reusable classification, priority scoring, action items, and drafting."""
        test_email = Email(
            id="TEST01",
            sender="prof.test@college.edu",
            subject="Urgent: Lab report submission tomorrow",
            body="Students must complete and submit lab report by tomorrow 5 PM.",
            received_at="2026-10-01T08:00:00"
        )
        analysis = self.skills.classify_email(test_email)
        self.assertEqual(analysis.category, "academic")
        self.assertIn(analysis.priority, ["HIGH", "CRITICAL", "MEDIUM"])

        scored = self.skills.score_priority(test_email, analysis)
        self.assertGreaterEqual(scored.urgency_score, 60)

        items = self.skills.extract_action_items(test_email)
        self.assertGreater(len(items), 0)

        draft = self.skills.draft_reply(test_email, scored)
        self.assertEqual(draft.status, "PENDING_APPROVAL")
        self.assertTrue(draft.subject.startswith("Re: "))

    def test_lab4_memory_and_retrieval(self):
        """Lab 4: Verify persistent SQLite storage and keyword/semantic retrieval."""
        self.memory.save_memory("test_key", "Important campus policy note.")
        results = self.memory.search("campus policy", limit=3)
        self.assertGreater(len(results), 0)
        found = any("campus policy" in str(r.get("body", "")).lower() for r in results)
        self.assertTrue(found)

    def test_lab5_mcp_style_connector(self):
        """Lab 5: Verify connector exposes tool descriptors and adapter fetches data."""
        tools_list = self.raw_connector.list_tools()
        names = [t["name"] for t in tools_list]
        self.assertIn("email.list", names)
        self.assertIn("email.get", names)
        self.assertIn("email.save_draft", names)

        emails = self.email_connector.list_emails()
        self.assertIsInstance(emails, list)


if __name__ == "__main__":
    unittest.main()
