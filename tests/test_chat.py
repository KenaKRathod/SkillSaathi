"""Tests for POST /chat endpoint — LLM is always mocked, no real API calls."""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agent_prompt import PROFILE_FIELDS
from app.state import clear_sessions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_sessions():
    """Ensure every test starts with a fresh session store."""
    clear_sessions()
    yield
    clear_sessions()


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app (import deferred so patches apply)."""
    from app.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_return(next_question, extracted_fields):
    """Return a dict mimicking the parsed LLM JSON response."""
    return {
        "next_question": next_question,
        "extracted_fields": extracted_fields,
    }


# ---------------------------------------------------------------------------
# Test: first call with empty profile → in_progress
# ---------------------------------------------------------------------------

class TestChatInProgress:
    @patch("app.main.call_llm")
    def test_first_call_returns_in_progress_with_next_question(
        self, mock_call_llm, client
    ):
        mock_call_llm.return_value = _make_llm_return(
            next_question="What is your current occupation?",
            extracted_fields={},
        )

        resp = client.post(
            "/chat",
            json={"session_id": "sess-1", "message": "Hello!"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_progress"
        assert "next_question" in body
        assert body["next_question"] == "What is your current occupation?"
        mock_call_llm.assert_called_once()


# ---------------------------------------------------------------------------
# Test: sequence that fills all fields → complete
# ---------------------------------------------------------------------------

class TestChatComplete:
    @patch("app.main.call_llm")
    def test_sequence_filling_all_fields_returns_complete(
        self, mock_call_llm, client
    ):
        """Simulate a multi-turn conversation where each turn fills one field.

        The final turn must return status: complete with the full profile.
        """
        # Each turn returns one extracted field and the next question.
        turns = [
            {
                "user_msg": "I'm an electrician",
                "llm_return": _make_llm_return(
                    next_question="How many years of experience do you have?",
                    extracted_fields={"occupation": "electrician"},
                ),
            },
            {
                "user_msg": "5 years",
                "llm_return": _make_llm_return(
                    next_question="What tools or machines can you use?",
                    extracted_fields={"years_experience": "5"},
                ),
            },
            {
                "user_msg": "Multimeter, wire stripper, pliers",
                "llm_return": _make_llm_return(
                    next_question="What is your highest education?",
                    extracted_fields={"tools_used": "multimeter, wire stripper, pliers"},
                ),
            },
            {
                "user_msg": "ITI diploma",
                "llm_return": _make_llm_return(
                    next_question="Which district do you live in?",
                    extracted_fields={"education": "ITI diploma"},
                ),
            },
            {
                "user_msg": "Ahmedabad",
                "llm_return": _make_llm_return(
                    next_question="What is your expected wage?",
                    extracted_fields={"district": "Ahmedabad"},
                ),
            },
            {
                "user_msg": "18000 per month",
                "llm_return": _make_llm_return(
                    next_question="Are you willing to travel or relocate?",
                    extracted_fields={"wage_goal": "18000/month"},
                ),
            },
            {
                "user_msg": "Can travel within Gujarat",
                "llm_return": _make_llm_return(
                    next_question=None,
                    extracted_fields={"mobility": "within Gujarat"},
                ),
            },
        ]

        session_id = "sess-full"

        for i, turn in enumerate(turns):
            mock_call_llm.return_value = turn["llm_return"]

            resp = client.post(
                "/chat",
                json={"session_id": session_id, "message": turn["user_msg"]},
            )
            assert resp.status_code == 200
            body = resp.json()

            if i < len(turns) - 1:
                # Intermediate turns must be in_progress
                assert body["status"] == "in_progress", (
                    f"Turn {i} should be in_progress, got {body}"
                )
                assert body["next_question"]
            else:
                # Final turn should be complete
                assert body["status"] == "complete", (
                    f"Final turn should be complete, got {body}"
                )
                profile = body["profile"]
                for field in PROFILE_FIELDS:
                    assert field in profile and profile[field], (
                        f"Profile missing field '{field}': {profile}"
                    )

    @patch("app.main.call_llm")
    def test_single_turn_fills_all_fields_returns_complete(
        self, mock_call_llm, client
    ):
        """Edge case: LLM fills every field in one go."""
        mock_call_llm.return_value = _make_llm_return(
            next_question=None,
            extracted_fields={
                "occupation": "plumber",
                "years_experience": "10",
                "tools_used": "wrench, pipe cutter",
                "education": "8th pass",
                "district": "Surat",
                "wage_goal": "20000/month",
                "mobility": "no relocation",
            },
        )

        resp = client.post(
            "/chat",
            json={"session_id": "sess-all-at-once", "message": "Here is everything"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "complete"
        assert set(PROFILE_FIELDS).issubset(set(body["profile"].keys()))


# ---------------------------------------------------------------------------
# Test: session isolation — different session_ids don't leak state
# ---------------------------------------------------------------------------

class TestSessionIsolation:
    @patch("app.main.call_llm")
    def test_different_sessions_have_independent_profiles(
        self, mock_call_llm, client
    ):
        # Session A fills occupation
        mock_call_llm.return_value = _make_llm_return(
            next_question="How many years of experience?",
            extracted_fields={"occupation": "welder"},
        )
        resp_a = client.post(
            "/chat", json={"session_id": "A", "message": "I weld"}
        )
        assert resp_a.json()["status"] == "in_progress"

        # Session B fills a different field
        mock_call_llm.return_value = _make_llm_return(
            next_question="What tools do you use?",
            extracted_fields={"occupation": "painter"},
        )
        resp_b = client.post(
            "/chat", json={"session_id": "B", "message": "I paint"}
        )
        assert resp_b.json()["status"] == "in_progress"

        # Session A should NOT have painter
        from app.state import SESSIONS
        assert SESSIONS["A"]["profile"]["occupation"] == "welder"
        assert SESSIONS["B"]["profile"]["occupation"] == "painter"


# ---------------------------------------------------------------------------
# Test: both LLM attempts fail → scripted fallback, not a 500
# ---------------------------------------------------------------------------

class TestRetryFallback:
    @patch("app.chat.genai")
    def test_both_attempts_fail_returns_fallback(self, mock_genai, client):
        """When the LLM raises on both retry attempts, the endpoint must
        return HTTP 200 with a scripted fallback question — never a 500.
        """
        mock_client = mock_genai.Client.return_value
        mock_client.models.generate_content.side_effect = RuntimeError(
            "LLM timeout"
        )

        resp = client.post(
            "/chat",
            json={"session_id": "sess-retry", "message": "Hello!"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_progress"
        assert body["next_question"]  # non-empty scripted question
        # Must have been called exactly twice (initial + 1 retry)
        assert mock_client.models.generate_content.call_count == 2


# ---------------------------------------------------------------------------
# Test: malformed JSON from LLM is handled gracefully
# ---------------------------------------------------------------------------

class TestMalformedJsonHandling:
    @patch("app.chat.genai")
    def test_malformed_json_response_returns_fallback(self, mock_genai, client):
        """If the LLM returns garbled non-JSON text, the endpoint should
        still return a 200 with a scripted fallback question.
        """
        mock_client = mock_genai.Client.return_value
        mock_response = type("Resp", (), {"text": "Sure! Here is your answer..."})()
        mock_client.models.generate_content.return_value = mock_response

        resp = client.post(
            "/chat",
            json={"session_id": "sess-bad-json", "message": "Hi"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_progress"
        assert body["next_question"]  # scripted fallback

    @patch("app.chat.genai")
    def test_json_embedded_in_text_is_recovered(self, mock_genai, client):
        """If the LLM wraps valid JSON inside surrounding prose, the regex
        fallback should extract and use it successfully.
        """
        embedded_json = json.dumps({
            "next_question": "How many years of experience?",
            "extracted_fields": {"occupation": "carpenter"},
        })
        raw_text = f"Here is the response:\n{embedded_json}\nHope this helps!"
        mock_client = mock_genai.Client.return_value
        mock_response = type("Resp", (), {"text": raw_text})()
        mock_client.models.generate_content.return_value = mock_response

        resp = client.post(
            "/chat",
            json={"session_id": "sess-embedded", "message": "I am a carpenter"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_progress"
        assert body["next_question"] == "How many years of experience?"


# ---------------------------------------------------------------------------
# Test: 3 consecutive empty extractions → redirect phrasing
# ---------------------------------------------------------------------------

class TestOffTopicRedirect:
    @patch("app.main.call_llm")
    def test_three_empty_extractions_trigger_redirect(
        self, mock_call_llm, client
    ):
        """After 3 consecutive turns where extracted_fields is empty, the
        next_question should be overwritten with a redirect prefix.
        """
        session_id = "sess-offtopic"

        # All three turns: LLM returns a question but extracts nothing
        for i in range(3):
            mock_call_llm.return_value = _make_llm_return(
                next_question=f"Interesting thought #{i + 1}!",
                extracted_fields={},
            )
            resp = client.post(
                "/chat",
                json={"session_id": session_id, "message": f"random chat {i}"},
            )
            assert resp.status_code == 200

        # The 3rd response must contain the redirect phrasing
        body = resp.json()
        assert body["next_question"].startswith("Let's get back to your work")

    @patch("app.main.call_llm")
    def test_redirect_resets_after_extraction(
        self, mock_call_llm, client
    ):
        """Verify that a successful extraction resets the empty streak,
        so the redirect does not fire prematurely after the reset.
        """
        session_id = "sess-reset"

        # 2 empty turns
        for _ in range(2):
            mock_call_llm.return_value = _make_llm_return(
                next_question="Tell me more?",
                extracted_fields={},
            )
            client.post(
                "/chat",
                json={"session_id": session_id, "message": "blah"},
            )

        # 1 turn WITH extraction → resets streak
        mock_call_llm.return_value = _make_llm_return(
            next_question="How many years of experience?",
            extracted_fields={"occupation": "driver"},
        )
        resp = client.post(
            "/chat",
            json={"session_id": session_id, "message": "I drive trucks"},
        )
        body = resp.json()
        assert not body["next_question"].startswith("Let's get back to your work")

        # 2 more empty turns — streak is only 2, redirect should NOT fire
        for _ in range(2):
            mock_call_llm.return_value = _make_llm_return(
                next_question="Hmm okay",
                extracted_fields={},
            )
            resp = client.post(
                "/chat",
                json={"session_id": session_id, "message": "something off topic"},
            )
        body = resp.json()
        assert not body["next_question"].startswith("Let's get back to your work")

