"""
Agent Chat API routes — chat (SSE), database connection, session management.
"""

import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from models.schemas import AgentChatRequest, DatabaseConnectRequest
from models.session import session_store
from services import agent_service
from services.database_service import connect_database, train_vanna_on_db

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat")
async def agent_chat(request: AgentChatRequest):
    """Stream agent response via SSE."""
    async def event_generator():
        async for event in agent_service.run_agent(
            message=request.message,
            session_id=request.session_id,
            file_id=request.file_id,
            source_type=request.source_type,
            pinned_mode=request.pinned_mode,
        ):
            evt_type = event.get("event", "message")
            data = event.get("data", "")
            if isinstance(data, dict):
                data = json.dumps(data)
            yield {"event": evt_type, "data": data}

    return EventSourceResponse(event_generator())


@router.post("/connect-db")
async def connect_db(request: DatabaseConnectRequest):
    """Connect to a database and train Vanna on its schema."""
    try:
        result = connect_database(request.connection_url)
        session = session_store.get(request.session_id)
        session.db_engine = result["engine"]
        session.db_tables = result["tables"]
        session.source_type = "database"

        # Train Vanna
        try:
            train_vanna_on_db(result["engine"])
        except Exception:
            pass  # Training failure is non-fatal

        return {
            "success": True,
            "tables": result["tables"],
            "message": f"Connected successfully. Found {len(result['tables'])} tables.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/state")
async def get_session_state(session_id: str):
    """Get current session state."""
    session = session_store.get(session_id)
    return {
        "session_id": session_id,
        "file_id": session.file_id,
        "source_type": session.source_type,
        "db_tables": session.db_tables,
        "db_connected": session.db_engine is not None,
        "canvas_output_count": len(session.canvas_outputs),
        "message_count": len(session.agent_conversation_history),
    }


@router.post("/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear canvas and conversation."""
    agent_service.clear_session(session_id)
    return {"message": "Session cleared."}
