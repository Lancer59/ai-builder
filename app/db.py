"""
SQLite storage using the built-in sqlite3 module.
Tables: agents, executions
"""
import sqlite3
import json
from contextlib import contextmanager
from app.models import Agent, Execution
from uuid import uuid4
from datetime import datetime

DB_PATH = "platform.db"

# --- Setup ---

def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                version TEXT NOT NULL,
                graph_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                input TEXT NOT NULL,
                output TEXT NOT NULL,
                logs TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# --- Agents ---

def save_agent(agent: Agent):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO agents VALUES (?,?,?,?,?)",
            (str(agent.id), agent.name, agent.version,
             json.dumps(agent.graph_json), agent.created_at.isoformat())
        )

def get_agent(name: str) -> Agent | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM agents WHERE name=?", (name,)).fetchone()
    if not row:
        return None
    return Agent(id=row["id"], name=row["name"], version=row["version"],
                 graph_json=json.loads(row["graph_json"]),
                 created_at=datetime.fromisoformat(row["created_at"]))

def list_agents() -> list[Agent]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM agents").fetchall()
    return [Agent(id=r["id"], name=r["name"], version=r["version"],
                  graph_json=json.loads(r["graph_json"]),
                  created_at=datetime.fromisoformat(r["created_at"])) for r in rows]

# --- Executions ---

def save_execution(ex: Execution):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO executions VALUES (?,?,?,?,?,?)",
            (str(ex.id), str(ex.agent_id), json.dumps(ex.input),
             json.dumps(ex.output), json.dumps(ex.logs), ex.status)
        )

def list_executions() -> list[Execution]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM executions").fetchall()
    return [Execution(id=r["id"], agent_id=r["agent_id"],
                      input=json.loads(r["input"]), output=json.loads(r["output"]),
                      logs=json.loads(r["logs"]), status=r["status"]) for r in rows]
