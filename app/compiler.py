"""
Graph Compiler — converts a validated AgentSpec into a LangGraph StateGraph.
"""
from langgraph.graph import StateGraph, END
from app.models import AgentSpec, Node
from app.tools import get_tool
from typing import TypedDict, Any


class AgentState(TypedDict):
    data: dict[str, Any]
    logs: list[str]


def _make_tool_node(tool_name: str):
    fn = get_tool(tool_name)

    def node_fn(state: AgentState) -> AgentState:
        result = fn(state["data"])
        logs = state["logs"] + [f"[{tool_name}] executed"]
        return {"data": result, "logs": logs}

    node_fn.__name__ = tool_name.replace(".", "_")
    return node_fn


def compile_graph(spec: AgentSpec):
    graph = StateGraph(AgentState)

    # Add nodes
    node_map: dict[str, str] = {}  # node id → graph node name
    for node in spec.nodes:
        if node.type == "input":
            name = f"input_{node.id}"
            graph.add_node(name, lambda s: s)  # passthrough
        elif node.type == "tool":
            name = node.tool.replace(".", "_")
            graph.add_node(name, _make_tool_node(node.tool))
        node_map[node.id] = name

    # Set entry point (first input node)
    input_node = next(n for n in spec.nodes if n.type == "input")
    graph.set_entry_point(node_map[input_node.id])

    # Add edges
    node_ids = {n.id for n in spec.nodes}
    for edge in spec.edges:
        src = node_map[edge.from_]
        dst = node_map[edge.to]
        graph.add_edge(src, dst)

    # Last node → END
    targets = {edge.to for edge in spec.edges}
    sources = {edge.from_ for edge in spec.edges}
    terminal_ids = targets - sources
    for nid in terminal_ids:
        graph.add_edge(node_map[nid], END)

    return graph.compile()
