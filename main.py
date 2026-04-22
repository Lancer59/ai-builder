from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from uuid import uuid4
from datetime import datetime

from app.models import BuildRequest, RunRequest, Agent, Execution
from app.ai_builder import build_agent_config, run_agent
from app.db import init_db, save_agent, get_agent, list_agents, save_execution, list_executions
from app.tools import ALL_TOOLS


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="AI Agent Platform", lifespan=lifespan)


@app.get("/tools")
def tools():
    """List all available tools."""
    return [{"name": t.name, "description": t.description} for t in ALL_TOOLS]


@app.post("/build")
def build(req: BuildRequest):
    """Natural language → agent (system prompt + tools auto-selected by AI) saved to DB."""
    config = build_agent_config(req.prompt)
    name = "_".join(req.prompt.lower().split()[:4]).replace("/", "")
    agent = Agent(
        id=uuid4(), name=name,
        system_prompt=config["system_prompt"],
        tools=config["tools"],
        created_at=datetime.utcnow(),
    )
    save_agent(agent)
    return agent


@app.get("/agents")
def agents():
    return list_agents()


@app.get("/agents/{name}")
def get_agent_by_name(name: str):
    agent = get_agent(name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    return agent


@app.post("/run")
def run(req: RunRequest):
    agent = get_agent(req.agent_name)
    if not agent:
        raise HTTPException(404, f"Agent '{req.agent_name}' not found")
    try:
        result = run_agent(agent.system_prompt, agent.tools, req.input)
        ex = Execution(id=uuid4(), agent_id=agent.id, input=req.input,
                       output=result["output"], logs=result["logs"], status="success")
    except Exception as e:
        ex = Execution(id=uuid4(), agent_id=agent.id, input=req.input,
                       output="", logs=[str(e)], status="failed")
    save_execution(ex)
    return ex


@app.get("/executions")
def executions():
    return list_executions()


@app.get("/", response_class=HTMLResponse)
def ui():
    with open("index.html") as f:
        return f.read()
