"""Planning node for LangGraph."""
from app.structure.pydantic import GraphState, NodeStatus

def planning_node(state: GraphState) -> GraphState:
    # Placeholder: generate research plan
    state.node_results.append({
        "node_name": "planning",
        "status": NodeStatus.COMPLETED,
        "output": {"plan": "..."},
        "retry_count": 0
    })
    return state
