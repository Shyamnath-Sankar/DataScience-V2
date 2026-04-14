"""
LangGraph state graph definition.
Wires together: Orchestrator → {EDA, Visualizer, Code, SQL, General}
"""

from langgraph.graph import StateGraph, START, END

from agents.state import AgentState
from agents.orchestrator import orchestrator_node
from agents.eda_agent import eda_agent_node
from agents.visualizer_agent import visualizer_agent_node
from agents.code_executor import code_executor_node
from agents.sql_agent import sql_agent_node
from agents.general_agent import general_agent_node


def _route_to_agent(state: AgentState) -> str:
    """Route from orchestrator to the classified agent."""
    intent = state.get("classified_intent", "general")
    routes = {
        "eda": "eda_agent",
        "visualization": "visualizer_agent",
        "code": "code_executor",
        "sql": "sql_agent",
        "general": "general_agent",
    }
    return routes.get(intent, "general_agent")


def build_agent_graph() -> StateGraph:
    """Build and compile the LangGraph agent state graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("eda_agent", eda_agent_node)
    graph.add_node("visualizer_agent", visualizer_agent_node)
    graph.add_node("code_executor", code_executor_node)
    graph.add_node("sql_agent", sql_agent_node)
    graph.add_node("general_agent", general_agent_node)

    # Edges
    graph.add_edge(START, "orchestrator")

    # Conditional routing from orchestrator
    graph.add_conditional_edges(
        "orchestrator",
        _route_to_agent,
        {
            "eda_agent": "eda_agent",
            "visualizer_agent": "visualizer_agent",
            "code_executor": "code_executor",
            "sql_agent": "sql_agent",
            "general_agent": "general_agent",
        },
    )

    # All agents → END
    graph.add_edge("eda_agent", END)
    graph.add_edge("visualizer_agent", END)
    graph.add_edge("code_executor", END)
    graph.add_edge("sql_agent", END)
    graph.add_edge("general_agent", END)

    return graph.compile()


# Compiled graph singleton
agent_graph = build_agent_graph()
