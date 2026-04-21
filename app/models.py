from pydantic import BaseModel, field_validator, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime


# --- Agent Spec (AI output / user-defined) ---

class Node(BaseModel):
    id: str
    type: str  # "input" | "tool"
    tool: Optional[str] = None  # required if type == "tool"

class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str

    model_config = {"populate_by_name": True}

class AgentSpec(BaseModel):
    agent_name: str
    nodes: list[Node]
    edges: list[Edge]

    @field_validator("nodes")
    @classmethod
    def must_have_input(cls, nodes):
        types = [n.type for n in nodes]
        assert "input" in types, "Must have at least one input node"
        return nodes

    @field_validator("edges")
    @classmethod
    def edges_not_empty(cls, edges):
        assert len(edges) > 0, "Must have at least one edge"
        return edges


# --- DB Models ---

class Agent(BaseModel):
    id: UUID = uuid4()
    name: str
    version: str = "v1"
    graph_json: dict
    created_at: datetime = datetime.utcnow()

class Execution(BaseModel):
    id: UUID = uuid4()
    agent_id: UUID
    input: dict
    output: dict = {}
    logs: list[str] = []
    status: str = "running"  # running | success | failed


# --- API Request/Response ---

class BuildRequest(BaseModel):
    prompt: str

class RunRequest(BaseModel):
    agent_name: str
    input: dict

class OrchestrateRequest(BaseModel):
    agent_names: list[str]
    input: dict
    mode: str = "sequential"
