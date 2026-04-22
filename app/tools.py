"""
Tool Registry — all tools available to agents.
Add new tools here; they become selectable in the builder.
"""
from langchain.tools import tool


@tool
def create_incident(description: str) -> str:
    """ServiceNow: create an incident. Returns the incident ID."""
    incident_id = f"INC{abs(hash(description)) % 100000:05d}"
    return f"Incident created: {incident_id} — '{description}'"


@tool
def assign_incident(incident_id: str, team: str = "network") -> str:
    """ServiceNow: assign an incident to a team."""
    return f"Incident {incident_id} assigned to team '{team}'"


@tool
def send_slack(message: str) -> str:
    """Slack: send a notification message to the default channel."""
    print(f"[Slack] {message}")
    return f"Slack notification sent: '{message}'"


# Registry — name → tool object (for UI listing)
ALL_TOOLS = [create_incident, assign_incident, send_slack]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}
