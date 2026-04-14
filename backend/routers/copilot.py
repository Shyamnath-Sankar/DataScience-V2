"""
Copilot API routes — chat (SSE), operation log, revert.
"""

import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from models.schemas import CopilotRequest
from models.session import session_store
from services import copilot_service

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


@router.post("/chat")
async def copilot_chat(request: CopilotRequest):
    """Stream copilot response via SSE."""
    async def event_generator():
        async for event in copilot_service.stream_chat(request):
            evt_type = event.get("event", "message")
            data = event.get("data", "")
            if isinstance(data, dict):
                data = json.dumps(data)
            yield {"event": evt_type, "data": data}

    return EventSourceResponse(event_generator())


@router.get("/{session_id}/operations")
async def get_operations(session_id: str):
    """Get the operation log for a session."""
    session = session_store.get(session_id)
    return {
        "operations": [op.model_dump(mode="json") for op in session.operations_log]
    }


@router.post("/{session_id}/revert/{operation_id}")
async def revert_operation(session_id: str, operation_id: str):
    """Revert a specific operation and all operations after it."""
    session = session_store.get(session_id)
    if not session.file_id:
        raise HTTPException(status_code=400, detail="No active file in this session.")

    try:
        result = copilot_service.revert_operation(
            file_id=session.file_id,
            operation_id=operation_id,
            session_id=session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/revert-last")
async def revert_last(session_id: str):
    """Revert the most recent operation."""
    session = session_store.get(session_id)
    if not session.file_id:
        raise HTTPException(status_code=400, detail="No active file in this session.")
    if not session.operations_log:
        raise HTTPException(status_code=400, detail="No operations to revert.")

    last_op = session.operations_log[-1]
    try:
        result = copilot_service.revert_operation(
            file_id=session.file_id,
            operation_id=last_op.id,
            session_id=session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
