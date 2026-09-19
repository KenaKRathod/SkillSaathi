"""Chat logic: LLM call, message building, and response parsing."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from google import genai

from app.agent_prompt import PROFILE_FIELDS, SYSTEM_PROMPT
from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scripted fallback questions — one per PROFILE_FIELD, in order
# ---------------------------------------------------------------------------

_SCRIPTED_QUESTIONS: Dict[str, str] = {
    "occupation": "What kind of work do you do?",
    "years_experience": "How many years of experience do you have?",
    "tools_used": "What tools or machines do you use in your work?",
    "education": "What is your highest level of education?",
    "district": "Which district or city do you live in?",
    "wage_goal": "What is your expected or desired wage?",
    "mobility": "Are you willing to travel or relocate for work?",
}


def get_scripted_question(profile: Optional[Dict[str, Any]] = None) -> str:
    """Return a generic question for the first unfilled PROFILE_FIELD.

    If *profile* is ``None`` or every field already has a value, fall back to
    the first question in the list.
    """
    profile = profile or {}
    for field in PROFILE_FIELDS:
        if not profile.get(field):
            return _SCRIPTED_QUESTIONS[field]
    # All fields filled (shouldn't normally reach here during profiling)
    return _SCRIPTED_QUESTIONS[PROFILE_FIELDS[0]]


def _fallback_result(profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build the scripted fallback dict used when the LLM is unavailable."""
    return {
        "next_question": get_scripted_question(profile),
        "extracted_fields": {},
    }


# ---------------------------------------------------------------------------
# Message building
# ---------------------------------------------------------------------------

def build_messages(
    history: List[Dict[str, str]], user_message: str
) -> List[Dict[str, str]]:
    """Build the message list for the LLM call.

    Returns a list of dicts with ``role`` and ``parts`` keys suitable for
    the google-genai ``client.models.generate_content`` API.
    """
    messages: List[Dict[str, str]] = []
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "parts": [{"text": user_message}]})
    return messages


# ---------------------------------------------------------------------------
# Robust JSON parsing (with regex fallback)
# ---------------------------------------------------------------------------

def parse_llm_response(text: str) -> Optional[Dict[str, Any]]:
    """Parse the raw LLM text into the expected JSON structure.

    Expected shape::

        {"next_question": str | None, "extracted_fields": {...}}

    Returns ``None`` if no valid JSON object can be recovered from *text*.
    """
    # 1. Attempt direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Regex fallback: try to extract the first JSON object from the text
    if text:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except (json.JSONDecodeError, TypeError):
                pass

    logger.warning("Failed to parse LLM response as JSON: %s", text[:200])
    return None


# ---------------------------------------------------------------------------
# LLM call with retry (max 2 attempts) and fallback
# ---------------------------------------------------------------------------

def call_llm(
    history: List[Dict[str, str]],
    user_message: str,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Send conversation to the Gemini LLM and return parsed JSON dict.

    Retries once on any exception.  If both attempts fail, or if the
    response cannot be parsed as JSON (even after regex recovery), a
    scripted fallback question is returned instead of raising.

    Args:
        history: Conversation history so far.
        user_message: The latest user utterance.
        profile: Current profile dict (used to pick the right fallback
            question for the next empty field).
    """
    messages = build_messages(history, user_message)
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        try:
            client = genai.Client(api_key=settings.llm_api_key)
            response = client.models.generate_content(
                model=settings.model_name,
                contents=messages,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                },
            )
            parsed = parse_llm_response(response.text)
            if parsed is not None:
                return parsed

            # Parsed to None → malformed JSON even after regex fallback
            logger.warning(
                "LLM returned unparseable response on attempt %d", attempt
            )
            return _fallback_result(profile)

        except Exception:
            logger.warning(
                "LLM call failed on attempt %d/%d",
                attempt,
                max_attempts,
                exc_info=True,
            )
            if attempt == max_attempts:
                return _fallback_result(profile)
            # Otherwise loop to retry

    # Should never reach here, but guard defensively
    return _fallback_result(profile)  # pragma: no cover
