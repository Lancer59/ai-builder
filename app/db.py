"""
SQLite storage. Tables: agents, executions
"""
import sqlite3
import json
from contextlib import contextmanager
from app.models import Agent, Execution
from datetime import datetime

DB_PATH = "platform.db"


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                system_prompt TEXT NOT NULL,
                tools TEXT NOT NULL,
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


def save_agent(agent: Agent):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO agents VALUES (?,?,?,?,?)",
            (str(agent.id), agent.name, agent.system_prompt,
             json.dumps(agent.tools), agent.created_at.isoformat())
        )


def get_agent(name: str) -> Agent | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM agents WHERE name=?", (name,)).fetchone()
    if not row:
        return None
    return Agent(id=row["id"], name=row["name"], system_prompt=row["system_prompt"],
                 tools=json.loads(row["tools"]),
                 created_at=datetime.fromisoformat(row["created_at"]))


def list_agents() -> list[Agent]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM agents").fetchall()
    return [Agent(id=r["id"], name=r["name"], system_prompt=r["system_prompt"],
                  tools=json.loads(r["tools"]),
                  created_at=datetime.fromisoformat(r["created_at"])) for r in rows]


def save_execution(ex: Execution):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO executions VALUES (?,?,?,?,?,?)",
            (str(ex.id), str(ex.agent_id), ex.input,
             ex.output, json.dumps(ex.logs), ex.status)
        )


def list_executions() -> list[Execution]:
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM executions").fetchall()
    return [Execution(id=r["id"], agent_id=r["agent_id"], input=r["input"],
                      output=r["output"], logs=json.loads(r["logs"]),
                      status=r["status"]) for r in rows]
