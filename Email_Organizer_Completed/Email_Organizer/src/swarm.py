import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from .models import Email, EmailAnalysis, ResearchDossier, DisciplineRecommendation
from .discipline_agents import AcademicAdvisorAgent, PlacementSpecialistAgent, AdministrativeOfficerAgent
from .runtime import AgentRuntime


class ParallelAgentSwarm:
    """
    Lab 8: Parallel Agent Swarm.
    
    Coordinates concurrent execution of specialized domain agents using
    a thread pool swarm, allowing multi-agent parallel processing.
    """

    def __init__(
        self,
        agents: List[Any],
        runtime: AgentRuntime,
        max_workers: int = 3
    ):
        self.agents = agents
        self.runtime = runtime
        self.max_workers = max_workers
        self.swarm_name = "ParallelDisciplineSwarm"

    def execute(
        self,
        emails: List[Email],
        analyses: Dict[str, EmailAnalysis],
        dossiers: Dict[str, ResearchDossier]
    ) -> Dict[str, List[DisciplineRecommendation]]:
        """Dispatch swarm tasks in parallel across all emails and discipline specialists."""
        start_time = time.perf_counter()
        results: Dict[str, List[DisciplineRecommendation]] = {email.id: [] for email in emails}
        thread_activity: Dict[str, List[str]] = {}
        lock = threading.Lock()

        tasks = []
        for email in emails:
            analysis = analyses.get(email.id)
            if not analysis:
                continue
            dossier = dossiers.get(email.id)
            for agent in self.agents:
                tasks.append((agent, email, analysis, dossier))

        def run_agent_task(agent, email, analysis, dossier):
            t_name = threading.current_thread().name
            res = agent.process(email, analysis, dossier)
            return t_name, agent.name, email.id, res

        self.runtime.log_event(
            "INFO",
            f"Spawning parallel swarm with {len(tasks)} sub-tasks across {self.max_workers} threads",
            agent=self.swarm_name
        )

        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="SwarmWorker") as executor:
            future_to_task = {
                executor.submit(run_agent_task, agent, email, analysis, dossier): (agent.name, email.id)
                for agent, email, analysis, dossier in tasks
            }

            for future in as_completed(future_to_task):
                try:
                    t_name, agent_name, email_id, rec = future.result()
                    with lock:
                        if t_name not in thread_activity:
                            thread_activity[t_name] = []
                        thread_activity[t_name].append(f"{agent_name} -> {email_id}")
                        if rec:
                            results[email_id].append(rec)
                except Exception as exc:
                    self.runtime.log_event("ERROR", f"Swarm task error: {exc}", agent=self.swarm_name)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        total_recs = sum(len(v) for v in results.values())

        self.runtime.track(
            self.swarm_name,
            "parallel_swarm_execution",
            start_time,
            details={
                "threads_used": len(thread_activity),
                "tasks_completed": len(tasks),
                "total_recommendations": total_recs,
                "thread_distribution": {k: len(v) for k, v in thread_activity.items()}
            }
        )

        return results
