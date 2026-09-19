# Changelog

## 2026-09-19 — Task-7: /chat fallback & retry logic
- **What changed:**
  - `call_llm` now retries the LLM call once on any exception; on second failure returns a scripted fallback question for the next empty profile field instead of raising.
  - `parse_llm_response` now attempts regex extraction of a JSON object when `json.loads` fails; returns `None` on total failure so the caller can substitute the fallback.
  - Added `get_scripted_question(profile)` — maps each `PROFILE_FIELD` to a generic human-friendly question.
  - `/chat` endpoint tracks `empty_streak` per session; after 3 consecutive turns with empty `extracted_fields`, overrides `next_question` with `"Let's get back to your work — {scripted question}"` and resets the counter.
  - Added 5 new tests (all mocked, no real API calls): double-exception fallback, malformed JSON handling, JSON-embedded-in-prose recovery, 3-empty redirect trigger, and streak reset after extraction.
- **Files touched:**
  - `app/chat.py`
  - `app/main.py`
  - `tests/test_chat.py`
  - `docs/CHANGELOG.md`
- **Why:**
  - Task-7 requirements: never expose a 500 on LLM failures, handle garbled JSON gracefully, and steer off-topic users back to profile building.
- **Contracts affected:** none (no changes to profile schema or endpoint shape).
- **Known issues / TODO:** none.

## 2026-09-19 — Add POST /transcribe and root endpoint
- **What changed:**
  - Added `POST /transcribe` endpoint with `faster-whisper` (`small` model, `language="auto"`).
  - Added silence, empty file, short duration (<0.5s), and corrupted audio file handling with clean HTTP responses (200 for no speech fallback, 400 for corrupted files, 503 for STT unavailability).
  - Added `GET /` root endpoint returning welcoming message with API links to `/docs` and `/health`.
  - Added `GET /favicon.ico` returning HTTP 204 No Content to prevent 404 logs when accessed via browsers.
  - Added automated test suite `tests/test_transcribe.py` with 7 tests and updated `tests/test_health.py` with root/favicon tests.
  - Added `faster-whisper>=1.0.0` and `gTTS>=2.2.0` to `requirements.txt`.
- **Files touched:**
  - `app/main.py`
  - `app/config.py`
  - `app/stt.py`
  - `requirements.txt`
  - `tests/test_transcribe.py`
  - `tests/test_health.py`
  - `.gitignore`
- **Why:**
  - Fulfill Task-2 STT transcription requirements and resolve 404 errors on root `/` and `/favicon.ico` when visited by a browser.
- **Contracts affected:**
  - Added `POST /transcribe` endpoint accepting multipart form-data `audio`.
- **Known issues / TODO:**
  - Stage 2: Conversational dialogue agent and state machine.

## 2026-09-19 — BE-03: API Contract for Frontend Integration
- **What changed:**
  - Created `api_contract.md` with Pydantic models and example JSON for all 7 endpoints: `POST /session`, `POST /stt`, `POST /turn`, `POST /readback`, `POST /confirm`, `POST /recommend`, `POST /tts`.
- **Files touched:**
  - `api_contract.md`
- **Why:**
  - Provide a clear, minimal contract for the frontend developer to build against.
- **Contracts affected:**
  - Formalized endpoint schemas for the 4-stage pipeline.
