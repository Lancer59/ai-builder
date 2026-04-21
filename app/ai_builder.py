"""
AI Builder — uses langchain.agents.create_agent with Azure OpenAI.
The agent's only tool is generate_agent_spec; it never executes workflow tools.
"""
import json
import os
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import AzureChatOpenAI
from app.models import AgentSpec
from app.tools import TOOLS

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

_llm = AzureChatOpenAI(
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    temperature=0,
)

_SYSTEM_PROMPT = f"""You are an expert workflow architect. Your ONLY job is to call the
generate_agent_spec tool with the user's prompt and return its output directly.

The tool will produce a JSON agent spec using ONLY these allowed tools:
{list(TOOLS.keys())}

Never add explanation. Never modify the JSON. Just call the tool and return the result."""


@tool
def generate_agent_spec(prompt: str) -> str:
    """Convert a natural language workflow description into a strict JSON agent spec."""
    allowed_tools = list(TOOLS.keys())
    system = f"""Convert the user's description into a JSON agent spec.

RULES:
1. Output ONLY raw JSON — no markdown, no explanation.
2. Only use tools from this list: {allowed_tools}
3. Node IDs are sequential strings: "1", "2", "3", ...
4. First node is always: {{"id": "1", "type": "input"}}
5. Tool nodes: {{"id": "N", "type": "tool", "tool": "<tool_name>"}}
6. Edges use "from" and "to" keys.

EXAMPLE — "create incident then notify slack":
{{
  "agent_name": "incident_notifier",
  "nodes": [
    {{"id": "1", "type": "input"}},
    {{"id": "2", "type": "tool", "tool": "servicenow.create_incident"}},
    {{"id": "3", "type": "tool", "tool": "slack.notify"}}
  ],
  "edges": [
    {{"from": "1", "to": "2"}},
    {{"from": "2", "to": "3"}}
  ]
}}"""
    response = _llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ])
    return response.content.strip()


_agent = create_agent(_llm, tools=[generate_agent_spec], system_prompt=_SYSTEM_PROMPT)


def build_agent_spec(prompt: str) -> AgentSpec:
    result = _agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    # Last message content is the final output
    raw = result["messages"][-1].content.strip()
    raw = raw.removeprefix("```json").removesuffix("```").strip()
    data = json.loads(raw)
    return AgentSpec.model_validate(data)
