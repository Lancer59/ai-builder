"""
AI Builder — two responsibilities:
1. build_system_prompt()  : LLM converts user description → system prompt for the agent
2. get_agent()            : returns a create_agent() instance ready to invoke
"""
import os
from langchain.agents import create_agent
from langchain_openai import AzureChatOpenAI
from app.tools import ALL_TOOLS, TOOL_MAP

from dotenv import load_dotenv
load_dotenv()

_llm = AzureChatOpenAI(
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    temperature=0,
)

def _tool_catalog() -> str:
    return "\n".join(f"- {t.name}: {t.description}" for t in ALL_TOOLS)


def build_agent_config(user_description: str) -> dict:
    """
    LLM reads the description + full tool catalog and returns:
      - system_prompt: what the agent should do
      - tools: which tool names are needed
    """
    system = f"""You are an AI agent designer. Given a user description, return a JSON object with:
1. "system_prompt": a concise system prompt (max 5 sentences) describing the agent's goal and behaviour.
2. "tools": a list of tool names (from the catalog) that this agent needs.

Available tools:
{_tool_catalog()}

Rules:
- Only include tools that are genuinely needed for the described workflow.
- Output ONLY valid JSON, no explanation, no markdown.

Example output:
{{"system_prompt": "You help manage IT incidents...", "tools": ["create_incident", "send_slack"]}}"""

    import json
    response = _llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": user_description},
    ])
    return json.loads(response.content.strip())


def get_agent(system_prompt: str, tool_names: list[str]):
    """Return a compiled create_agent() graph for the given prompt + tools."""
    tools = [TOOL_MAP[n] for n in tool_names if n in TOOL_MAP]
    return create_agent(_llm, tools=tools, system_prompt=system_prompt)


def run_agent(system_prompt: str, tool_names: list[str], user_input: str) -> dict:
    """Invoke the agent and return output + tool call log."""
    agent = get_agent(system_prompt, tool_names)
    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})

    messages = result.get("messages", [])
    logs = []
    for m in messages:
        # capture tool calls as log entries
        if hasattr(m, "tool_calls") and m.tool_calls:
            for tc in m.tool_calls:
                logs.append(f"[tool] {tc['name']}({tc['args']})")
        elif hasattr(m, "name") and m.name:  # ToolMessage
            logs.append(f"[result] {m.content}")

    final = messages[-1].content if messages else ""
    return {"output": final, "logs": logs}
