"""
AI Builder — LLM reads the MCP tool catalog, picks relevant tools,
writes a system prompt, then create_agent() wires it all together.
"""
import json
import os
from langchain.agents import create_agent
from langchain_openai import AzureChatOpenAI
from app.mcp_loader import load_mcp_tools, get_tool_catalog

from dotenv import load_dotenv
load_dotenv()

_llm = AzureChatOpenAI(
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    temperature=0,
)


async def build_agent_config(user_description: str) -> dict:
    """
    1. Load all tools from MCP servers
    2. LLM picks which tools are needed + writes a system prompt
    3. Returns { system_prompt, tools: [names], tool_objects: [...] }
    """
    all_tools = await load_mcp_tools()
    catalog = get_tool_catalog(all_tools)
    tool_map = {t.name: t for t in all_tools}

    response = _llm.invoke([
        {"role": "system", "content": f"""You are an AI agent designer.
Given a user description and a list of available tools, return a JSON object with:
1. "system_prompt": concise agent instructions (max 5 sentences).
2. "tools": list of tool names from the catalog that this agent needs.

Available tools:
{catalog}

Output ONLY valid JSON, no markdown. Example:
{{"system_prompt": "You help manage IT incidents...", "tools": ["tool_a", "tool_b"]}}"""},
        {"role": "user", "content": user_description},
    ])

    config = json.loads(response.content.strip())
    config["tool_objects"] = [tool_map[n] for n in config["tools"] if n in tool_map]
    return config


async def run_agent(system_prompt: str, tool_names: list[str], user_input: str) -> dict:
    """Load MCP tools, build the agent, invoke it, return output + logs."""
    all_tools = await load_mcp_tools()
    tool_map = {t.name: t for t in all_tools}
    tools = [tool_map[n] for n in tool_names if n in tool_map]

    agent = create_agent(_llm, tools=tools, system_prompt=system_prompt)
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})

    messages = result.get("messages", [])
    logs = []
    for m in messages:
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                logs.append(f"[tool] {tc['name']}({tc['args']})")
        elif hasattr(m, "name") and m.name:
            logs.append(f"[result] {m.content}")

    return {"output": messages[-1].content if messages else "", "logs": logs}
