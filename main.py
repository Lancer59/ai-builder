from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from uuid import uuid4
from datetime import datetime

from app.models import BuildRequest, RunRequest, Agent, Execution
from app.ai_builder import build_agent_config, run_agent
from app.mcp_loader import load_mcp_tools
from app.db import init_db, save_agent, get_agent, list_agents, save_execution, list_executions


logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="AI Agent Platform", lifespan=lifespan)


@app.get("/tools")
async def tools():
    """List all tools loaded from configured MCP servers."""
    all_tools = await load_mcp_tools()
    return [{"name": t.name, "description": t.description} for t in all_tools]


@app.post("/build")
async def build(req: BuildRequest):
    """Natural language → agent config (LLM picks tools + writes prompt) → saved to DB."""
    config = await build_agent_config(req.prompt)
    agent = Agent(
        id=uuid4(), name=req.name,
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
async def run(req: RunRequest):
    agent = get_agent(req.agent_name)
    if not agent:
        raise HTTPException(404, f"Agent '{req.agent_name}' not found")
    try:
        result = await run_agent(agent.system_prompt, agent.tools, req.input)
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
