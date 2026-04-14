"""
In-memory session store.
All state is kept in Python dicts — no external DB needed.
"""

from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class SessionState:
    session_id: str
    file_id: Optional[str] = None
    dataframe: Optional[pd.DataFrame] = None
    operations_log: list = field(default_factory=list)
    agent_conversation_history: list = field(default_factory=list)
    canvas_outputs: list = field(default_factory=list)
    dataset_profile_cache: Optional[dict] = None
    db_engine: Optional[Any] = None
    db_tables: list = field(default_factory=list)
    source_type: str = "file"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    def touch(self):
        self.last_accessed = datetime.utcnow()


class SessionStore:
    def __init__(self, ttl_hours: int = 24):
        self._sessions: dict[str, SessionState] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        session = self._sessions[session_id]
        session.touch()
        return session

    def delete(self, session_id: str):
        self._sessions.pop(session_id, None)

    def cleanup_expired(self):
        now = datetime.utcnow()
        expired = [
            sid for sid, state in self._sessions.items()
            if now - state.last_accessed > self._ttl
        ]
        for sid in expired:
            # Dispose DB engines if present
            if self._sessions[sid].db_engine:
                try:
                    self._sessions[sid].db_engine.dispose()
                except Exception:
                    pass
            del self._sessions[sid]
        return len(expired)


# Global store singleton
session_store = SessionStore()
