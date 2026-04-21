from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from app.models import BuildRequest, RunRequest, OrchestrateRequest, Agent, AgentSpec
from app.ai_builder import build_agent_spec
from app.executor import run_agent, run_sequential
from app.db import save_agent, get_agent, list_agents, save_execution, list_executions, init_db
from uuid import uuid4
from datetime import datetime

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="AI Agent Workflow Platform", lifespan=lifespan)


# --- AI Builder ---

@app.post("/build")
def build(req: BuildRequest):
    """Convert a natural language prompt into a validated agent spec."""
    spec = build_agent_spec(req.prompt)
    agent = Agent(
        id=uuid4(),
        name=spec.agent_name,
        graph_json=spec.model_dump(),
        created_at=datetime.utcnow(),
    )
    save_agent(agent)
    return {"agent": agent, "spec": spec}


# --- Agent Management ---

@app.get("/agents")
def agents():
    return list_agents()

@app.get("/agents/{name}")
def get_agent_by_name(name: str):
    agent = get_agent(name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    return agent


@app.post("/agents")
def create_agent(spec: AgentSpec):
    """Manually save a validated agent spec."""
    agent = Agent(id=uuid4(), name=spec.agent_name, graph_json=spec.model_dump())
    save_agent(agent)
    return agent


# --- Execution ---

@app.post("/run")
def run(req: RunRequest):
    agent = get_agent(req.agent_name)
    if not agent:
        raise HTTPException(404, f"Agent '{req.agent_name}' not found")
    spec = AgentSpec.model_validate(agent.graph_json)
    result = run_agent(spec, req.input)
    result.agent_id = agent.id
    save_execution(result)
    return result


# --- Orchestration ---

@app.post("/orchestrate")
def orchestrate(req: OrchestrateRequest):
    if req.mode != "sequential":
        raise HTTPException(400, "Only 'sequential' mode is supported")
    specs = []
    for name in req.agent_names:
        agent = get_agent(name)
        if not agent:
            raise HTTPException(404, f"Agent '{name}' not found")
        specs.append(AgentSpec.model_validate(agent.graph_json))
    results = run_sequential(specs, req.input)
    for r in results:
        save_execution(r)
    return results


# --- Logs ---

@app.get("/executions")
def executions():
    return list_executions()


# --- UI ---

@app.get("/", response_class=HTMLResponse)
def ui():
    with open("index.html") as f:
        return f.read()
