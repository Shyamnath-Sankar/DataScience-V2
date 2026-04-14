"""
Agent service: runs the LangGraph graph and manages sessions.
"""

import json
from typing import AsyncGenerator

import pandas as pd

from config import settings
from models.session import session_store
from services import file_service
from agents.graph import agent_graph
from agents.state import AgentState


def _build_dataframe_summary(df: pd.DataFrame) -> dict:
    """Build a compact summary for the LLM (never the full dataframe)."""
    summary = {
        "shape": {"rows": len(df), "cols": len(df.columns)},
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "sample_rows": df.head(5).where(df.head(5).notna(), None).to_dict(orient="records"),
        "null_counts": {col: int(df[col].isnull().sum()) for col in df.columns},
    }
    return summary


async def run_agent(
    message: str,
    session_id: str,
    file_id: str | None = None,
    source_type: str = "file",
    pinned_mode: str | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Run the LangGraph agent and yield SSE events.
    """
    session = session_store.get(session_id)

    # Load data
    df = None
    dataframe_summary = {}

    if source_type == "file" and file_id:
        try:
            df = file_service.load_dataframe(file_id)
            session.file_id = file_id
            session.dataframe = df

            # Use cached profile or build new one
            if session.dataset_profile_cache and session.file_id == file_id:
                dataframe_summary = session.dataset_profile_cache
            else:
                dataframe_summary = _build_dataframe_summary(df)
                session.dataset_profile_cache = dataframe_summary

        except ValueError as e:
            yield {"event": "error", "data": str(e)}
            return

    elif source_type == "database":
        df = session.dataframe  # May be None for DB — SQL agent uses engine directly
        if session.dataset_profile_cache:
            dataframe_summary = session.dataset_profile_cache

    if not dataframe_summary and df is not None:
        dataframe_summary = _build_dataframe_summary(df)

    # Build initial state
    initial_state: AgentState = {
        "user_message": message,
        "session_id": session_id,
        "source_type": source_type,
        "file_id": file_id,
        "dataframe_summary": dataframe_summary,
        "conversation_history": session.agent_conversation_history[-20:],
        "pinned_mode": pinned_mode,
        "classified_intent": None,
        "sse_events": [],
        "result": None,
        "dataframe": df,
        "db_engine": session.db_engine,
    }

    # Run the graph
    try:
        result = await agent_graph.ainvoke(initial_state)

        # Yield all accumulated SSE events
        for event in result.get("sse_events", []):
            yield event

        # Update session
        session.agent_conversation_history.append({"role": "user", "content": message})
        if result.get("result"):
            result_data = result["result"]
            session.canvas_outputs.append(result_data)

            # Build a concise assistant message from the result
            if result_data.get("type") == "text":
                assistant_msg = result_data.get("data", {}).get("content", "")
            else:
                assistant_msg = f"[Generated {result_data.get('type', 'output')}]"
            session.agent_conversation_history.append({"role": "assistant", "content": assistant_msg})

    except Exception as e:
        yield {"event": "error", "data": "Something went wrong running that analysis. Try rephrasing your question."}

    yield {"event": "done", "data": ""}


def clear_session(session_id: str):
    """Clear canvas and conversation for a session."""
    session = session_store.get(session_id)
    session.agent_conversation_history = []
    session.canvas_outputs = []
    session.dataset_profile_cache = None
