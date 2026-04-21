# AI Agent Workflow Platform

Convert natural language into executable AI agent workflows using Azure OpenAI + LangGraph.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your Azure OpenAI credentials
```

## Run

```bash
uvicorn main:app --reload
```

Open `http://localhost:8000` to use the visual builder.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Visual workflow builder UI |
| `POST` | `/build` | Prompt → agent spec + save |
| `GET` | `/agents` | List saved agents |
| `POST` | `/agents` | Save agent spec manually |
| `POST` | `/run` | Execute an agent |
| `POST` | `/orchestrate` | Run agents sequentially |
| `GET` | `/executions` | Execution logs |

## Stack

- **FastAPI** — API + UI serving
- **LangGraph** — workflow execution engine
- **LangChain + Azure OpenAI** — natural language → agent spec
- **SQLite** — persistent storage (agents + executions)
- **Cytoscape.js** — graph visualization
