"""Chat logic: LLM call, message building, and response parsing."""

import json
from typing import Any, Dict, List

from google import genai

from app.agent_prompt import SYSTEM_PROMPT
from app.config import settings


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


def call_llm(
    history: List[Dict[str, str]], user_message: str
) -> Dict[str, Any]:
    """Send conversation to the Gemini LLM and return parsed JSON dict.

    Happy-path only — assumes the LLM always returns valid JSON.
    """
    messages = build_messages(history, user_message)
    client = genai.Client(api_key=settings.llm_api_key)
    response = client.models.generate_content(
        model=settings.model_name,
        contents=messages,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
        },
    )
    return parse_llm_response(response.text)


def parse_llm_response(text: str) -> Dict[str, Any]:
    """Parse the raw LLM text into the expected JSON structure.

    Expected shape::

        {"next_question": str | None, "extracted_fields": {...}}
    """
    return json.loads(text)
