"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
import uuid


# ── File Models ──────────────────────────────────────────────


class ColumnInfo(BaseModel):
    name: str
    dtype: str  # "number", "text", "date", "boolean"
    sample_values: list[str] = []


class FileRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str  # stored name (uuid.ext)
    original_name: str
    row_count: int
    col_count: int
    columns: list[ColumnInfo]
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_size: int = 0  # bytes


class FilePreview(BaseModel):
    file_id: str
    columns: list[ColumnInfo]
    rows: list[dict[str, Any]]
    total_rows: int
    total_cols: int


# ── Copilot Models ───────────────────────────────────────────


class OperationParams(BaseModel):
    """Generic params container for copilot operations."""
    type: str  # add_row, update_cell, update_cells_bulk, delete_rows, add_column, rename_column
    params: dict[str, Any] = {}


class Operation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str
    type: str
    description: str  # plain English: "Added row · Raju · Oct · ₹52,000"
    params: dict[str, Any] = {}
    inverse_data: dict[str, Any] = {}  # data needed to revert
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CopilotRequest(BaseModel):
    message: str
    session_id: str
    file_id: str


class CopilotResponse(BaseModel):
    reply: str
    operation: Optional[Operation] = None
    redirect: bool = False
    updated_rows: Optional[list[dict[str, Any]]] = None


# ── Agent Models ─────────────────────────────────────────────


class AgentChatRequest(BaseModel):
    message: str
    session_id: str
    file_id: Optional[str] = None
    source_type: str = "file"  # "file" or "database"
    pinned_mode: Optional[str] = None  # None = auto


class DatabaseConnectRequest(BaseModel):
    connection_url: str
    session_id: str


class CanvasOutput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # chart, table, eda, code_output, sql_output, text
    agent_name: str
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Common ───────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    message: str
    detail: Optional[str] = None
