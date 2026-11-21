import time
from typing import Dict, Any, List
from .models import QATestResult, WorkflowState
from .runtime import AgentRuntime
from .tools import ToolRegistry


class QualityAssuranceAgent:
    """
    Lab 11: Agentic SDLC Factory and Testing Agent.
    
    Executes automated quality verification, schema assertions, regression checks,
    and contract tests across all agent outputs in the workflow.
    """

    def __init__(self, tools: ToolRegistry, runtime: AgentRuntime):
        self.name = "QualityAssuranceAgent"
        self.tools = tools
        self.runtime = runtime

    def run_tests(self, state: WorkflowState) -> List[QATestResult]:
        """Execute full automated test suite against the current workflow state."""
        start_time = time.perf_counter()
        results: List[QATestResult] = []

        # Test 1: Ingestion Schema Integrity
        t1_start = time.perf_counter()
        t1_passed = True
        t1_msg = "All emails conform to standard schema (id, sender, subject, body, received_at)."
        for email in state.emails:
            if not email.id or not email.sender or "@" not in email.sender or not email.subject:
                t1_passed = False
                t1_msg = f"Email {email.id} failed schema integrity check."
                break
        results.append(QATestResult(
            test_id="SDLC-001",
            test_name="Ingestion Schema Integrity",
            category="Schema",
            passed=t1_passed,
            message=t1_msg,
            duration_ms=round((time.perf_counter() - t1_start) * 1000, 2)
        ))

        # Test 2: Triage Classification Contract
        t2_start = time.perf_counter()
        t2_passed = True
        t2_msg = "All emails classified with valid category and priority."
        valid_priorities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        valid_categories = {"academic", "administrative", "placement", "meeting", "information", "other"}
        for eid, analysis in state.analyses.items():
            if analysis.priority not in valid_priorities or analysis.category not in valid_categories:
                t2_passed = False
                t2_msg = f"Analysis for {eid} has invalid priority '{analysis.priority}' or category '{analysis.category}'."
                break
        results.append(QATestResult(
            test_id="SDLC-002",
            test_name="Triage Classification Contract",
            category="Contract",
            passed=t2_passed,
            message=t2_msg,
            duration_ms=round((time.perf_counter() - t2_start) * 1000, 2)
        ))

        # Test 3: Urgency Score Boundary Assertion (0-100)
        t3_start = time.perf_counter()
        t3_passed = True
        t3_msg = "All urgency scores reside strictly in [0, 100] boundary."
        for eid, analysis in state.analyses.items():
            if not (0 <= analysis.urgency_score <= 100):
                t3_passed = False
                t3_msg = f"Urgency score {analysis.urgency_score} for {eid} out of bounds."
                break
        results.append(QATestResult(
            test_id="SDLC-003",
            test_name="Urgency Boundary Assertion",
            category="Assertion",
            passed=t3_passed,
            message=t3_msg,
            duration_ms=round((time.perf_counter() - t3_start) * 1000, 2)
        ))

        # Test 4: Human-in-the-Loop Security Guardrail
        t4_start = time.perf_counter()
        t4_passed = True
        t4_msg = "Zero emails dispatched automatically. All drafts require human approval."
        for draft in state.drafts:
            if draft.status != "PENDING_APPROVAL":
                t4_passed = False
                t4_msg = f"Draft for {draft.email_id} has unauthorized status '{draft.status}'."
                break
        results.append(QATestResult(
            test_id="SDLC-004",
            test_name="Human Approval Guardrail",
            category="Security",
            passed=t4_passed,
            message=t4_msg,
            duration_ms=round((time.perf_counter() - t4_start) * 1000, 2)
        ))

        # Test 5: Draft Content Completeness & Form
        t5_start = time.perf_counter()
        t5_passed = True
        t5_msg = "All generated drafts have valid recipient, subject, and non-empty body."
        for draft in state.drafts:
            if not draft.to or not draft.subject.startswith("Re: ") or len(draft.body.strip()) < 15:
                t5_passed = False
                t5_msg = f"Draft for {draft.email_id} incomplete or badly formed."
                break
        results.append(QATestResult(
            test_id="SDLC-005",
            test_name="Draft Content Completeness",
            category="Quality",
            passed=t5_passed,
            message=t5_msg,
            duration_ms=round((time.perf_counter() - t5_start) * 1000, 2)
        ))

        # Test 6: Memory Retrieval Contract
        t6_start = time.perf_counter()
        t6_passed = True
        t6_msg = "Memory retrieval query executed and returned valid structured records."
        try:
            sample_query = self.tools.call("search_memory", query="placement deadline", limit=2)
            if not isinstance(sample_query, list):
                t6_passed = False
                t6_msg = "search_memory returned non-list data."
        except Exception as e:
            t6_passed = False
            t6_msg = f"Memory retrieval failed: {e}"
        results.append(QATestResult(
            test_id="SDLC-006",
            test_name="Memory Retrieval Contract",
            category="Integration",
            passed=t6_passed,
            message=t6_msg,
            duration_ms=round((time.perf_counter() - t6_start) * 1000, 2)
        ))

        # Test 7: Multi-Agent Coverage Test
        t7_start = time.perf_counter()
        t7_passed = (len(state.emails) > 0) and (len(state.analyses) == len(state.emails))
        t7_msg = f"100% email coverage across Triage and Multi-Agent Swarm ({len(state.analyses)}/{len(state.emails)})."
        results.append(QATestResult(
            test_id="SDLC-007",
            test_name="Multi-Agent Coverage Verification",
            category="Coverage",
            passed=t7_passed,
            message=t7_msg,
            duration_ms=round((time.perf_counter() - t7_start) * 1000, 2)
        ))

        self.tools.call(
            "audit_log",
            agent_name=self.name,
            action="sdlc_automated_testing",
            details={
                "total_tests": len(results),
                "passed": sum(1 for r in results if r.passed),
                "failed": sum(1 for r in results if not r.passed)
            }
        )

        self.runtime.track(
            self.name,
            "execute_sdlc_test_suite",
            start_time,
            details={"pass_rate": f"{sum(1 for r in results if r.passed)}/{len(results)}"}
        )
        return results
