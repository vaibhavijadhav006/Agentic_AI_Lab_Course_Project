import unittest
from pathlib import Path
from src.models import WorkflowState, Email, Draft
from src.storage import MemoryStore
from src.connectors.json_connector import JSONEmailConnector
from src.connectors.mcp_style_adapter import MCPStyleEmailAdapter
from src.skills import EmailSkills
from src.tools import ToolRegistry
from src.runtime import AgentRuntime
from src.graph import NodeGraphOrchestrator, GraphNode
from src.swarm import ParallelAgentSwarm
from src.research import DeepResearchAgent
from src.cloud_ops import CloudOpsMonitor
from src.sdlc import QualityAssuranceAgent
from src.safety import SafetyGovernanceAgent
from src.discipline_agents import (
    AcademicAdvisorAgent,
    PlacementSpecialistAgent,
    AdministrativeOfficerAgent
)
from src.final import FinalReportGenerator


class TestAll14Labs(unittest.TestCase):
    """Test suite verifying integration of Labs 6 to 14."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.data_dir = cls.base_dir / "data"
        cls.memory = MemoryStore(cls.data_dir / "test_14labs_memory.db")
        cls.raw_connector = JSONEmailConnector(cls.data_dir / "emails.json")
        cls.connector = MCPStyleEmailAdapter(cls.raw_connector)
        cls.skills = EmailSkills()
        cls.tools = ToolRegistry(cls.connector, cls.memory)
        cls.runtime = AgentRuntime(cls.data_dir)

    @classmethod
    def tearDownClass(cls):
        cls.memory.close()
        test_db = cls.data_dir / "test_14labs_memory.db"
        if test_db.exists():
            try:
                test_db.unlink()
            except Exception:
                pass

    def test_lab6_runtime_telemetry(self):
        """Lab 6: Verify AgentRuntime tracks latency, logs events, and compiles telemetry."""
        record = self.runtime.track("TestAgent", "test_action", 0.0, "SUCCESS")
        self.assertEqual(record.status, "SUCCESS")
        metrics = self.runtime.get_monitoring_metrics()
        self.assertIn("total_agent_invocations", metrics)
        self.assertIn("average_latency_ms", metrics)

    def test_lab7_node_graph_orchestration(self):
        """Lab 7: Verify NodeGraphOrchestrator manages state transitions across pipeline."""
        graph = NodeGraphOrchestrator(self.runtime)
        def node1_handler(state):
            state.metrics["n1"] = True
            return state
        def node2_handler(state):
            state.metrics["n2"] = True
            return state
        graph.add_node(GraphNode("n1", "Node 1", "desc", node1_handler))
        graph.add_node(GraphNode("n2", "Node 2", "desc", node2_handler))
        graph.add_edge("n1", "n2")
        graph.set_execution_pipeline(["n1", "n2"])
        
        final_state = graph.run(WorkflowState())
        self.assertTrue(final_state.metrics.get("n1"))
        self.assertTrue(final_state.metrics.get("n2"))

    def test_lab8_parallel_agent_swarm(self):
        """Lab 8: Verify ParallelAgentSwarm executes agents concurrently and merges state."""
        acad = AcademicAdvisorAgent(self.tools, self.runtime)
        place = PlacementSpecialistAgent(self.tools, self.runtime)
        admin = AdministrativeOfficerAgent(self.tools, self.runtime)
        swarm = ParallelAgentSwarm([acad, place, admin], self.runtime, max_workers=3)

        raw = self.tools.call("list_emails")
        emails = [Email(**e) for e in raw]
        analyses = {e.id: self.skills.classify_email(e) for e in emails}
        dossiers = {}

        results = swarm.execute(emails, analyses, dossiers)
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), len(emails))

    def test_lab9_deep_research_agent(self):
        """Lab 9: Verify DeepResearchAgent gathers context, expands queries, and provides citations."""
        research = DeepResearchAgent(self.tools, self.runtime, self.skills.llm)
        email = Email("E001", "prof@college.edu", "Project review meeting - Friday", "Please prepare milestone report", "2026-10-01")
        dossier = research.investigate(email)
        self.assertGreater(len(dossier.query_expanded), 0)
        self.assertGreater(len(dossier.citations), 0)
        self.assertIn("Evidence", dossier.findings)

    def test_lab10_cloud_ops_resilience(self):
        """Lab 10: Verify CloudOpsMonitor tracks circuit breakers, health checks, and SLA metrics."""
        monitor = CloudOpsMonitor(self.runtime)
        health = monitor.perform_health_checks(storage_connected=True, data_file_exists=True)
        self.assertEqual(health["overall_status"], "HEALTHY")
        summary = monitor.get_summary()
        self.assertEqual(summary["circuit_breakers"]["connector"], "CLOSED")

    def test_lab11_sdlc_factory_testing(self):
        """Lab 11: Verify QualityAssuranceAgent executes CI/CD regression assertions."""
        qa = QualityAssuranceAgent(self.tools, self.runtime)
        raw = self.tools.call("list_emails")
        emails = [Email(**e) for e in raw]
        analyses = {e.id: self.skills.score_priority(e, self.skills.classify_email(e)) for e in emails}
        drafts = [Draft(e.id, e.sender, f"Re: {e.subject}", "Thank you for the notification.") for e in emails]
        
        state = WorkflowState(emails=emails, analyses=analyses, drafts=drafts)
        test_results = qa.run_tests(state)
        self.assertEqual(len(test_results), 7)
        passed = sum(1 for t in test_results if t.passed)
        self.assertEqual(passed, 7)

    def test_lab12_safety_and_governance(self):
        """Lab 12: Verify SafetyGovernanceAgent detects PII and enforces PENDING_APPROVAL status."""
        safety = SafetyGovernanceAgent(self.tools, self.runtime)
        safe_draft = Draft("E001", "prof@college.edu", "Re: Review", "Thank you.", "PENDING_APPROVAL")
        rec = safety.audit_draft(safe_draft)
        self.assertEqual(rec.risk_level, "LOW")
        self.assertTrue(rec.human_approval_required)

        # Attempt unauthorized status
        tampered_draft = Draft("E002", "prof@college.edu", "Re: Review", "Password is secret123", "SENT")
        rec2 = safety.audit_draft(tampered_draft)
        self.assertEqual(tampered_draft.status, "PENDING_APPROVAL")  # Enforced rollback
        self.assertEqual(rec2.risk_level, "HIGH")

    def test_lab13_discipline_specific_agents(self):
        """Lab 13: Verify academic, placement, and admin agents apply specialized domain logic."""
        acad = AcademicAdvisorAgent(self.tools, self.runtime)
        place = PlacementSpecialistAgent(self.tools, self.runtime)
        
        acad_email = Email("E003", "faculty@college.edu", "Question about your assignment", "BFS or DFS?", "2026-10-01")
        acad_analysis = self.skills.classify_email(acad_email)
        rec_acad = acad.process(acad_email, acad_analysis)
        self.assertIsNotNone(rec_acad)
        self.assertEqual(rec_acad.discipline, "academic")

        place_email = Email("E004", "placement@college.edu", "Action required: placement registration", "Submit by tomorrow", "2026-10-01")
        place_analysis = self.skills.classify_email(place_email)
        rec_place = place.process(place_email, place_analysis)
        self.assertIsNotNone(rec_place)
        self.assertEqual(rec_place.discipline, "placement")

    def test_lab14_final_capstone_report_generation(self):
        """Lab 14: Verify FinalReportGenerator produces final.json and final.md."""
        final_gen = FinalReportGenerator(self.data_dir)
        raw = self.tools.call("list_emails")
        emails = [Email(**e) for e in raw]
        analyses = {e.id: self.skills.classify_email(e) for e in emails}
        drafts = [Draft(e.id, e.sender, f"Re: {e.subject}", "Thank you.") for e in emails]
        state = WorkflowState(emails=emails, analyses=analyses, drafts=drafts)
        
        report = final_gen.generate(state, self.runtime, {"environment": "Local Cloud"}, {})
        self.assertIn("14_labs" if "14_labs" in report else "lab_integration_matrix", report)
        self.assertTrue(final_gen.final_json_path.exists())
        self.assertTrue(final_gen.final_md_path.exists())


if __name__ == "__main__":
    unittest.main()
