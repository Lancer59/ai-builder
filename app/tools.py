"""
Tool Registry — maps tool names to Python functions.
All tools are stateless and receive/return dicts.
"""

def create_incident(state: dict) -> dict:
    """ServiceNow: create an incident."""
    incident_id = f"INC{hash(str(state)) % 100000:05d}"
    return {**state, "incident_id": incident_id, "status": "created"}


def assign_incident(state: dict) -> dict:
    """ServiceNow: assign incident to a team."""
    team = state.get("team", "network")
    return {**state, "assigned_to": team, "status": "assigned"}


def send_slack(state: dict) -> dict:
    """Slack: send a notification message."""
    msg = state.get("message", f"Incident {state.get('incident_id')} update")
    print(f"[Slack] {msg}")
    return {**state, "slack_sent": True}


# Central registry
TOOLS: dict[str, callable] = {
    "servicenow.create_incident": create_incident,
    "servicenow.assign_incident": assign_incident,
    "slack.notify": send_slack,
}


def get_tool(name: str) -> callable:
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: '{name}'. Allowed: {list(TOOLS)}")
    return TOOLS[name]
