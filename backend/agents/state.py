"""
LangGraph shared agent state definition.
"""

from typing import TypedDict, Optional, Annotated, Any, List, Dict
import operator


class AgentState(TypedDict):
    """Shared state passed between all LangGraph nodes."""
    user_message: str
    session_id: str
    source_type: str  # "file" or "database"
    file_id: Optional[str]
    dataframe_summary: dict  # schema, dtypes, shape, 5-row sample
    conversation_history: list[dict]
    pinned_mode: Optional[str]  # None = auto, or "eda"/"visualization"/"code"/"sql"
    classified_intent: Optional[str]
    # Accumulated SSE events — uses operator.add so each node appends
    sse_events: Annotated[list[dict], operator.add]
    result: Optional[dict]  # Final output for canvas
    # The actual dataframe (not passed to LLM, used by agents)
    dataframe: Optional[Any]
    # DB engine for SQL agent
    db_engine: Optional[Any]
    
    # === NEW: Planner & Skills Support ===
    task_plan: Optional[Dict]  # Current task plan with progress tracking
    current_task: Optional[Dict]  # Task currently being executed
    task_result: Optional[Dict]  # Result from the most recent task execution
    all_tasks_complete: bool  # Flag indicating all tasks are done
