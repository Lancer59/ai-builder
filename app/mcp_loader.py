"""
MCP Tool Loader — reads mcp_servers.json and loads all tools as LangChain tools
using langchain-mcp-adapters. Supports stdio, http, and sse transports.
"""
import json
import logging
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)
MCP_CONFIG_PATH = Path("mcp_servers.json")


def _load_config() -> dict:
    if not MCP_CONFIG_PATH.exists():
        return {}
    return json.loads(MCP_CONFIG_PATH.read_text()).get("servers", {})


async def load_mcp_tools() -> list:
    """Connect to all configured MCP servers and return LangChain tools.
    Servers that fail to connect are skipped with a warning."""
    servers = _load_config()
    if not servers:
        return []

    tools = []
    for name, config in servers.items():
        try:
            client = MultiServerMCPClient({name: config})
            server_tools = await client.get_tools()
            logger.info("Server '%s' loaded %d tool(s): %s", name, len(server_tools), [t.name for t in server_tools])
            tools.extend(server_tools)
        except Exception as e:
            logger.warning("Skipping server '%s': %s", name, e)
    return tools


def get_tool_catalog(tools: list) -> str:
    """Format tools into a readable catalog string for the LLM."""
    if not tools:
        return "No tools available."
    return "\n".join(f"- {t.name}: {t.description}" for t in tools)
