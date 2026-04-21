"""
Execution Engine — runs compiled graphs and returns structured results.
"""
from app.models import AgentSpec, Execution
from app.compiler import compile_graph, AgentState
from uuid import uuid4


def run_agent(spec: AgentSpec, input_data: dict) -> Execution:
    graph = compile_graph(spec)
    initial_state: AgentState = {"data": input_data, "logs": []}

    try:
        result = graph.invoke(initial_state)
        return Execution(
            id=uuid4(),
            agent_id=uuid4(),  # replaced by real ID when stored
            input=input_data,
            output=result["data"],
            logs=result["logs"],
            status="success",
        )
    except Exception as e:
        return Execution(
            id=uuid4(),
            agent_id=uuid4(),
            input=input_data,
            output={},
            logs=[f"ERROR: {e}"],
            status="failed",
        )


def run_sequential(specs: list[AgentSpec], input_data: dict) -> list[Execution]:
    """Run multiple agents sequentially, passing output as next input."""
    results = []
    state = input_data
    for spec in specs:
        exec_result = run_agent(spec, state)
        results.append(exec_result)
        if exec_result.status == "failed":
            break
        state = exec_result.output  # chain state
    return results
