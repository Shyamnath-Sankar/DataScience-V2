"""
LangGraph state graph definition.
Supports two modes:
1. Simple Routing: Orchestrator → Agent (for quick queries)
2. Planner Mode: Orchestrator → Planner → Task Loop → Report (for complex analysis)
"""

from langgraph.graph import StateGraph, START, END

from agents.state import AgentState
from agents.orchestrator import orchestrator_node
from agents.eda_agent import eda_agent_node
from agents.visualizer_agent import visualizer_agent_node
from agents.code_executor import code_executor_node
from agents.sql_agent import sql_agent_node
from agents.general_agent import general_agent_node
from agents.planner import plan_tasks, execute_next_task, complete_task, compile_final_report


def _route_to_agent(state: AgentState) -> str:
    """Route from orchestrator to the classified agent or planner."""
    intent = state.get("classified_intent", "general")
    
    # Check if this requires planning (complex multi-step analysis)
    user_msg = state.get("user_message", "").lower()
    complex_keywords = ["eda", "exploratory data analysis", "analyze", "machine learning", 
                       "model", "prediction", "comprehensive", "full analysis", 
                       "dashboard", "clean data", "prepare data"]
    
    requires_planning = any(kw in user_msg for kw in complex_keywords)
    
    if requires_planning:
        return "planner"
    
    routes = {
        "eda": "eda_agent",
        "visualization": "visualizer_agent",
        "code": "code_executor",
        "sql": "sql_agent",
        "general": "general_agent",
    }
    return routes.get(intent, "general_agent")


def _should_continue_task_loop(state: AgentState) -> str:
    """Decide whether to continue task loop or finish."""
    all_complete = state.get("all_tasks_complete", False)
    if all_complete:
        return "compile_report"
    return "execute_task"


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
    
    # Planner nodes
    graph.add_node("planner", plan_tasks)
    graph.add_node("execute_task", execute_next_task)
    graph.add_node("agent_task_executor", _route_task_to_agent)
    graph.add_node("complete_task", complete_task)
    graph.add_node("compile_report", compile_final_report)

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
            "planner": "planner",
        },
    )

    # Simple agents → END
    graph.add_edge("eda_agent", END)
    graph.add_edge("visualizer_agent", END)
    graph.add_edge("code_executor", END)
    graph.add_edge("sql_agent", END)
    graph.add_edge("general_agent", END)
    
    # Planner flow
    graph.add_edge("planner", "execute_task")
    
    # Task execution loop
    graph.add_conditional_edges(
        "execute_task",
        _should_continue_task_loop,
        {
            "execute_task": "agent_task_executor",
            "compile_report": "compile_report",
        }
    )
    
    # Agent executes current task
    graph.add_edge("agent_task_executor", "complete_task")
    
    # Loop back to check for more tasks
    graph.add_edge("complete_task", "execute_task")
    
    # Final report → END
    graph.add_edge("compile_report", END)

    return graph.compile()


def _route_task_to_agent(state: AgentState) -> dict:
    """Route current task to appropriate agent based on task type."""
    current_task = state.get("current_task", {})
    target_agent = current_task.get("target_agent", "general")
    
    # Update state with enhanced prompt for the agent
    enhanced_prompt = current_task.get("enhanced_prompt", "")
    if enhanced_prompt:
        # Temporarily override user_message for this task
        state["user_message"] = enhanced_prompt
    
    # Route to appropriate agent
    agent_map = {
        "visualization": "visualizer_agent",
        "code": "code_executor",
        "eda": "eda_agent",
        "general": "general_agent",
        "sql": "sql_agent"
    }
    
    target_node = agent_map.get(target_agent, "general_agent")
    
    # We'll use a subgraph or direct execution here
    # For now, return state with marker for which agent to use
    state["_task_target_agent"] = target_node
    return state


# Compiled graph singleton
agent_graph = build_agent_graph()
