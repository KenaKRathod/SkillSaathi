"""In-memory session state management with max-size eviction fallback."""

from typing import Any, Dict, Optional
from app.config import settings

# Global in-memory session store mapping session_id -> profile dict
SESSIONS: Dict[str, Dict[str, Any]] = {}

DEFAULT_MAX_SESSIONS: int = getattr(settings, "max_sessions", 1000)


def get_session(session_id: str, max_sessions: Optional[int] = None) -> Dict[str, Any]:
    """Retrieve an existing session or create a new session dict.

    If session_id already exists in SESSIONS, return the existing dict object.
    If session_id does not exist:
      - If capacity is reached (len(SESSIONS) >= limit), evict the oldest session
        (FIFO/LRU eviction) to prevent unbounded memory growth.
      - Create a new empty profile dict for session_id.
      - Store it in SESSIONS and return the dict object.

    Args:
        session_id: Unique string identifier for the session.
        max_sessions: Optional maximum session capacity override. Defaults to config.

    Returns:
        dict: The mutable session dictionary for session_id.
    """
    limit = max_sessions if max_sessions is not None else DEFAULT_MAX_SESSIONS

    if session_id in SESSIONS:
        # Move session to end to mark as recently accessed (LRU ordering)
        session = SESSIONS.pop(session_id)
        SESSIONS[session_id] = session
        return session

    # Eviction fallback if SESSIONS reaches or exceeds max capacity
    while len(SESSIONS) >= limit and SESSIONS:
        oldest_id = next(iter(SESSIONS))
        del SESSIONS[oldest_id]

    new_profile: Dict[str, Any] = {}
    SESSIONS[session_id] = new_profile
    return new_profile


def clear_sessions() -> None:
    """Clear all active sessions (useful for tests and resets)."""
    SESSIONS.clear()
