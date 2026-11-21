import unittest
from pathlib import Path
from src.storage import MemoryStore
from src.connectors.json_connector import JSONEmailConnector
from src.connectors.mcp_style_adapter import MCPStyleEmailAdapter
from src.tools import ToolRegistry


class TestInteractiveOperations(unittest.TestCase):
    """Test suite verifying interactive operations and draft approval mechanics."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.data_dir = cls.base_dir / "data"
        cls.memory = MemoryStore(cls.data_dir / "test_menu_memory.db")
        cls.raw_connector = JSONEmailConnector(cls.data_dir / "emails.json")
        cls.connector = MCPStyleEmailAdapter(cls.raw_connector)
        cls.tools = ToolRegistry(cls.connector, cls.memory)

    @classmethod
    def tearDownClass(cls):
        cls.memory.close()
        test_db = cls.data_dir / "test_menu_memory.db"
        if test_db.exists():
            try:
                test_db.unlink()
            except Exception:
                pass

    def test_save_and_approve_draft(self):
        """Verify saving a draft queues it as PENDING_APPROVAL and approval updates status."""
        draft = {
            "email_id": "TEST_E01",
            "to": "test@college.edu",
            "subject": "Re: Test Subject",
            "body": "This is a test draft for approval verification.",
            "status": "PENDING_APPROVAL"
        }
        res = self.tools.call("save_draft", draft=draft)
        self.assertEqual(res["status"], "saved")

        # Verify initial status
        saved = self.memory.get_draft("TEST_E01")
        self.assertIsNotNone(saved)
        self.assertEqual(saved["status"], "PENDING_APPROVAL")

        # Approve draft
        ok = self.memory.update_draft_status("TEST_E01", "APPROVED")
        self.assertTrue(ok)

        # Verify approved status
        approved = self.memory.get_draft("TEST_E01")
        self.assertEqual(approved["status"], "APPROVED")

    def test_search_and_retrieve_email(self):
        """Verify search operations return matched emails and notes."""
        self.memory.save_analysis(
            {"id": "TEST_SEARCH", "sender": "search@college.edu", "subject": "Graph Traversal BFS", "body": "Uses BFS", "received_at": "2026-10-01"},
            {"category": "academic", "priority": "MEDIUM", "urgency_score": 60, "action_items": [], "reply_required": False}
        )
        results = self.memory.search("Graph Traversal", limit=3)
        self.assertGreater(len(results), 0)
        found = any("Graph Traversal" in r.get("subject", "") for r in results)
        self.assertTrue(found)

    def test_memory_storage_and_retrieval(self):
        """Verify arbitrary memory key-value pairs are stored and retrieved."""
        self.tools.call("save_memory", key="campus_wifi", value="Use eduroam with college login")
        res = self.tools.call("search_memory", query="eduroam", limit=2)
        self.assertGreater(len(results) if (results := res) else 0, 0)

    def test_persistent_menu_reappears_after_each_action(self):
        """Verify the 16-option interactive menu reappears after each operation."""
        import subprocess, sys
        inputs = "1\n3\nBFS\n5\n16\n"
        res = subprocess.run(
            [sys.executable, "-m", "src.main"],
            input=inputs,
            cwd=str(self.base_dir),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        menu_tag = "AGENTIC EMAIL ORGANIZER - INTERACTIVE MODE"
        count = res.stdout.count(menu_tag)
        # Appeared initially, after option 1, after option 3, and after option 5 = 4 times
        self.assertEqual(count, 4)
        self.assertIn("ALL EMAILS IN INBOX", res.stdout)
        self.assertIn("SEARCH RESULTS FOR", res.stdout)
        self.assertIn("DRAFT REPLY QUEUE", res.stdout)


if __name__ == "__main__":
    unittest.main()
