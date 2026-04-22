"""
Example FastMCP stdio server — replace with your real MCP servers.
Run standalone: python example_mcp_server.py
Referenced in mcp_servers.json under "example_stdio".
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example")


@mcp.tool()
def create_incident(description: str) -> str:
    """ServiceNow: create an incident and return its ID."""
    return f"INC{abs(hash(description)) % 100000:05d}"


@mcp.tool()
def assign_incident(incident_id: str, team: str = "network") -> str:
    """ServiceNow: assign an incident to a team."""
    return f"Incident {incident_id} assigned to '{team}'"


@mcp.tool()
def send_slack(message: str) -> str:
    """Slack: send a notification to the default channel."""
    return f"Slack sent: {message}"


if __name__ == "__main__":
    mcp.run()
