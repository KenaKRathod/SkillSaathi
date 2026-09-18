"""Tests for FastAPI health endpoint, CORS, in-memory sessions, and settings."""

import asyncio
import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.state import SESSIONS, get_session, clear_sessions
from app.config import Settings


@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure in-memory sessions are cleared before and after each test."""
    clear_sessions()
    yield
    clear_sessions()


def test_health_returns_200_and_ok():
    """GET /health returns 200 and {"status": "ok"} using TestClient (httpx)."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_httpx_async_client():
    """GET /health returns 200 and {"status": "ok"} using direct httpx.AsyncClient."""
    async def _run():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    asyncio.run(_run())


def test_get_session_twice_same_id_returns_same_dict_object():
    """Calling get_session() twice with the same id returns the same dict object."""
    session_id = "user_session_101"

    session_1 = get_session(session_id)
    session_2 = get_session(session_id)

    # Both references point to the exact same mutable dict in memory
    assert session_1 is session_2
    assert id(session_1) == id(session_2)

    # Modifying one reference updates the session
    session_1["user_id"] = "U101"
    session_1["skills"] = ["Python", "FastAPI"]

    assert session_2["user_id"] == "U101"
    assert session_2["skills"] == ["Python", "FastAPI"]


def test_get_session_new_id_creates_empty_profile_dict():
    """Calling get_session() with a new id creates an empty profile dict."""
    session_id = "user_session_fresh"

    session = get_session(session_id)

    assert isinstance(session, dict)
    assert session == {}
    assert len(session) == 0


def test_cors_enabled_for_localhost_5173():
    """CORS is configured and enabled for http://localhost:5173."""
    client = TestClient(app)

    # Simple GET request with Origin header
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Preflight OPTIONS request
    preflight = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_session_eviction_max_size():
    """When SESSIONS reaches capacity, oldest session is evicted to prevent memory leak."""
    # Test capacity limit of 2 sessions
    s1 = get_session("sess_1", max_sessions=2)
    s1["data"] = "data 1"

    s2 = get_session("sess_2", max_sessions=2)
    s2["data"] = "data 2"

    assert len(SESSIONS) == 2
    assert "sess_1" in SESSIONS
    assert "sess_2" in SESSIONS

    # Adding a 3rd session should trigger eviction of the oldest ("sess_1")
    s3 = get_session("sess_3", max_sessions=2)
    s3["data"] = "data 3"

    assert len(SESSIONS) == 2
    assert "sess_1" not in SESSIONS
    assert "sess_2" in SESSIONS
    assert "sess_3" in SESSIONS


def test_settings_loaded_from_env(monkeypatch):
    """Pydantic Settings loads LLM API key and model name from environment."""
    monkeypatch.setenv("LLM_API_KEY", "sk-mock-key-12345")
    monkeypatch.setenv("MODEL_NAME", "gemini-2.0-flash")

    test_settings = Settings()
    assert test_settings.llm_api_key == "sk-mock-key-12345"
    assert test_settings.model_name == "gemini-2.0-flash"
    assert test_settings.llm_model_name == "gemini-2.0-flash"
