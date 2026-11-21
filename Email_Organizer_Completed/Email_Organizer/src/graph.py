import time
from typing import Dict, Any, List, Callable, Optional
from .models import WorkflowState, Email, Draft
from .runtime import AgentRuntime


class GraphNode:
    """A discrete, executable node in the agentic workflow DAG."""

    def __init__(self, node_id: str, name: str, description: str, handler: Callable[[WorkflowState], WorkflowState]):
        self.node_id = node_id
        self.name = name
        self.description = description
        self.handler = handler

    def execute(self, state: WorkflowState) -> WorkflowState:
        return self.handler(state)


class NodeGraphOrchestrator:
    """
    Lab 7: Agentic Node Graph Orchestration.
    
    Coordinates end-to-end execution across discrete nodes using a directed
    state graph, passing a shared WorkflowState across all stages.
    """

    def __init__(self, runtime: AgentRuntime):
        self.runtime = runtime
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[tuple[str, str]] = []
        self.execution_order: List[str] = []

    def add_node(self, node: GraphNode):
        self.nodes[node.node_id] = node

    def add_edge(self, from_node: str, to_node: str):
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError(f"Invalid edge: {from_node} -> {to_node}")
        self.edges.append((from_node, to_node))

    def set_execution_pipeline(self, pipeline: List[str]):
        """Define topological sequence of node execution."""
        for nid in pipeline:
            if nid not in self.nodes:
                raise ValueError(f"Node '{nid}' not found in registered graph nodes.")
        self.execution_order = pipeline

    def describe_topology(self) -> Dict[str, Any]:
        """Describe nodes, edges, and pipeline for architectural visibility."""
        return {
            "total_nodes": len(self.nodes),
            "nodes": [
                {"id": n.node_id, "name": n.name, "description": n.description}
                for n in self.nodes.values()
            ],
            "edges": [{"from": e[0], "to": e[1]} for e in self.edges],
            "pipeline": self.execution_order
        }

    def run(self, initial_state: Optional[WorkflowState] = None) -> WorkflowState:
        """Run through all nodes in the DAG sequentially, updating state."""
        state = initial_state or WorkflowState()
        graph_start = time.perf_counter()

        self.runtime.log_event(
            "INFO",
            f"Initiating Node Graph execution with pipeline: {' -> '.join(self.execution_order)}",
            agent="NodeGraphOrchestrator"
        )

        for idx, node_id in enumerate(self.execution_order, start=1):
            node = self.nodes[node_id]
            node_start = time.perf_counter()
            self.runtime.log_event("INFO", f"Entering Node: {node.name}", agent="NodeGraphOrchestrator")
            
            state = node.execute(state)
            
            node_duration = (time.perf_counter() - node_start) * 1000.0
            self.runtime.log_event(
                "INFO",
                f"Exited Node: {node.name} ({node_duration:.2f}ms)",
                agent="NodeGraphOrchestrator"
            )

        total_elapsed = (time.perf_counter() - graph_start) * 1000.0
        state.metrics["graph_execution_duration_ms"] = round(total_elapsed, 2)
        state.metrics["nodes_executed_count"] = len(self.execution_order)

        self.runtime.track(
            "NodeGraphOrchestrator",
            "complete_graph_run",
            graph_start,
            details={"nodes": len(self.execution_order), "duration_ms": round(total_elapsed, 2)}
        )

        return state
