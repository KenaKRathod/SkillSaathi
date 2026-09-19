"""Tests for app.agent_prompt — no LLM calls required."""

import pytest

from app.agent_prompt import PROFILE_FIELDS, SYSTEM_PROMPT, is_profile_complete


# ---------------------------------------------------------------------------
# Fixture: a fully-filled profile dict
# ---------------------------------------------------------------------------
@pytest.fixture
def full_profile() -> dict:
    return {
        "occupation": "electrician",
        "years_experience": "5",
        "tools_used": "multimeter, pliers",
        "education": "ITI diploma",
        "district": "Ahmedabad",
        "wage_goal": "18000/month",
        "mobility": "willing to travel within Gujarat",
    }


# ---------------------------------------------------------------------------
# is_profile_complete – positive case
# ---------------------------------------------------------------------------
class TestIsProfileComplete:
    def test_returns_true_when_all_fields_filled(self, full_profile: dict):
        assert is_profile_complete(full_profile) is True

    # --- negative cases: each field missing one at a time ----------------
    @pytest.mark.parametrize("missing_field", PROFILE_FIELDS)
    def test_returns_false_when_field_is_missing(
        self, full_profile: dict, missing_field: str
    ):
        incomplete = {k: v for k, v in full_profile.items() if k != missing_field}
        assert is_profile_complete(incomplete) is False

    @pytest.mark.parametrize("missing_field", PROFILE_FIELDS)
    def test_returns_false_when_field_is_empty_string(
        self, full_profile: dict, missing_field: str
    ):
        full_profile[missing_field] = ""
        assert is_profile_complete(full_profile) is False

    @pytest.mark.parametrize("missing_field", PROFILE_FIELDS)
    def test_returns_false_when_field_is_none(
        self, full_profile: dict, missing_field: str
    ):
        full_profile[missing_field] = None
        assert is_profile_complete(full_profile) is False

    def test_returns_false_for_empty_dict(self):
        assert is_profile_complete({}) is False


# ---------------------------------------------------------------------------
# SYSTEM_PROMPT validation
# ---------------------------------------------------------------------------
class TestSystemPrompt:
    def test_system_prompt_is_non_empty(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT.strip()) > 0

    @pytest.mark.parametrize("field", PROFILE_FIELDS)
    def test_system_prompt_mentions_every_profile_field(self, field: str):
        assert field in SYSTEM_PROMPT, (
            f"SYSTEM_PROMPT does not mention the profile field '{field}'"
        )
