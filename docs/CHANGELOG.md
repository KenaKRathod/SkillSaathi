# Changelog

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
