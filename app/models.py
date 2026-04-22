from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime


# --- DB Models ---

class Agent(BaseModel):
    id: UUID = uuid4()
    name: str
    system_prompt: str
    tools: list[str]          # tool names selected for this agent
    created_at: datetime = datetime.utcnow()


class Execution(BaseModel):
    id: UUID = uuid4()
    agent_id: UUID
    input: str
    output: str = ""
    logs: list[str] = []
    status: str = "running"   # running | success | failed


# --- API Requests ---

class BuildRequest(BaseModel):
    name: str
    prompt: str

class RunRequest(BaseModel):
    agent_name: str
    input: str                         # plain text input to the agent
