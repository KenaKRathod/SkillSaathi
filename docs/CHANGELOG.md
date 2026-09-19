# Changelog

## 2026-09-19 — Audio Playback Wiring with `/tts` API
- **What changed:**
  - Modified `RecommendationsScreen` to POST top recommendation's reasoning text to `http://localhost:8000/tts` after loading real results.
  - Added conditional `<audio>` player rendering when `/tts` returns `audio_available: true`.
  - Implemented fallback omitting the `<audio>` player when `audio_available` is `false`, missing, or when `/tts` POST fails.
  - Added automated RTL unit test suite (`src/components/RecommendationsScreen.test.jsx`) verifying `audio_available: true` renders audio player and `audio_available: false` / missing field renders no player.
- **Files touched:**
  - `src/components/RecommendationsScreen.jsx`
  - `src/components/RecommendationsScreen.test.jsx`
  - `docs/CHANGELOG.md`
- **Why:**
  - Complete Task-20 optional audio playback wiring for spoken recommendation summaries with fallback support.
- **Contracts affected:** none
- **Known issues / TODO:** none

## 2026-09-19 — Wire Recommendations Screen to `/recommend` API
- **What changed:**
  - Updated `RecommendationsScreen` to POST `{ category_result, profile }` to `http://localhost:8000/recommend` on component mount.
  - Replaced mock array with real response payload (`programs`, `relaxed_filters`, `audio_url`).
  - Added loading indicator state while awaiting `/recommend` response.
  - Added fetch failure error card with a **Retry** button that re-issues the POST request.
  - Preserved Task-17 fallback views (`relaxed_filters` banner, audio player, empty array no-match message).
  - Updated `App.jsx` to pass confirmed `categoryResult` and `profile` down to `RecommendationsScreen`.
  - Added RTL test suite (`src/components/RecommendationsScreen.test.jsx`) verifying mount POST call, real cards rendering, and failed fetch Retry functionality.
- **Files touched:**
  - `src/components/RecommendationsScreen.jsx`
  - `src/App.jsx`
  - `src/components/RecommendationsScreen.test.jsx`
  - `docs/CHANGELOG.md`
- **Why:**
  - Complete Task-18 final frontend wiring connecting confirmed category + profile to the `/recommend` endpoint.
- **Contracts affected:** none
- **Known issues / TODO:** none

## 2026-09-19 — Build Recommendations Screen UI with Mock Data
- **What changed:**
  - Implemented Recommendations screen rendering 3 default mock program cards (`name`, `scheme`, `nsqf_level`, `duration`, `reasoning`).
  - Added support for rendering an optional `relaxed_filters` / `relaxedFiltersNote` banner above the program cards.
  - Added support for rendering an optional `<audio>` player when `audio_url` / `audioUrl` is present.
  - Added fallback view for empty program arrays (`programs = []`) rendering a "No matching programs found yet" message and a "Back to Chat" button.
  - Added automated RTL unit test suite (`src/components/RecommendationsScreen.test.jsx`) covering 3 cards rendering, relaxed filters note conditional display, audio player rendering, and empty array fallback navigation.
- **Files touched:**
  - `src/components/RecommendationsScreen.jsx`
  - `src/App.jsx`
  - `src/App.css`
  - `src/components/RecommendationsScreen.test.jsx`
  - `docs/CHANGELOG.md`
- **Why:**
  - Build Task-17 Recommendations screen UI against mock data with relaxed filters note, audio player, empty state fallback, and RTL test coverage.
- **Contracts affected:** none
- **Known issues / TODO:** none

## 2026-09-19 — Wire Confirm Screen to Map Skills API
- **What changed:**
  - Updated the confirm form flow to POST the reviewed profile to `http://localhost:8000/map-skills`.
  - Added category-result handling that forwards the server response to the next screen via `onNext`.
  - Added clarification follow-up handling: when the backend returns `needs_clarification`, a one-off question and answer field appear and the profile is re-submitted with the extra answer.
  - Kept the legacy `onConfirm` callback behavior for existing screen-level tests and callback wiring.
- **Files touched:**
  - `src/components/ConfirmScreen.jsx`
  - `src/components/ConfirmScreen.test.jsx`
  - `docs/CHANGELOG.md`
- **Why:**
  - Connect the profile confirmation UI to the mapper endpoint and support the low-confidence clarification flow from the backend.
- **Contracts affected:** none
- **Known issues / TODO:**
  - Task 18 will finalize the recommendations navigation and result rendering.

## 2026-09-19 — Build Chat Screen with `/chat` API & Fallbacks
- **What changed:**
  - Implemented Chat screen with session ID state (`session_id`).
  - Integrated `POST http://localhost:8000/chat` sending `{ session_id, message }` on user input and displaying user and assistant chat bubbles.
  - Implemented completion navigation (`status: "complete"`), passing profile data up to `ConfirmScreen`.
  - Added inline `"Didn't catch that — try again"` prompt handling for `onTranscript(null)` without triggering `/chat`.
  - Added fetch failure handling with a **Retry** button that re-sends the last user message.
  - Added RTL unit test suite (`src/components/ChatScreen.test.jsx`) verifying chat bubbles rendering, null transcript prompt behavior, failed request retry functionality, and completion handoff.
- **Files touched:**
  - `src/components/ChatScreen.jsx`
  - `src/App.jsx`
  - `src/components/ConfirmScreen.jsx`
  - `src/App.css`
  - `src/components/ChatScreen.test.jsx`
  - `docs/CHANGELOG.md`
- **Why:**
  - Build frontend chat conversation workflow, agent API communication, retry mechanisms, and RTL tests.
- **Contracts affected:** none
- **Known issues / TODO:** none

## 2026-09-19 — Build MicButton Component with STT Integration & Fallback Mode
- **What changed:**
  - Built `<MicButton>` component supporting `MediaRecorder` audio recording lifecycle (press to start, press to stop).
  - Configured audio blob upload via multipart POST to `http://localhost:8000/transcribe`.
  - Added handling for `no_speech_detected` response calling `onTranscript(null)` to prompt user retry.
  - Implemented recording pulse indicator dot and loading spinner UI states.
  - Implemented `textFallbackMode` rendering plain text `<input>` and submit button calling `onTranscript(typedText)`.
  - Integrated `<MicButton>` in `ChatScreen` with message list and retry prompt.
  - Added RTL test suite (`src/components/MicButton.test.jsx`) with mock fetch and MediaRecorder verifying successful transcription, `no_speech_detected` `null` callback, and `textFallbackMode` rendering.
- **Files touched:**
  - `src/components/MicButton.jsx`
  - `src/components/ChatScreen.jsx`
  - `src/App.css`
  - `src/components/MicButton.test.jsx`
  - `docs/CHANGELOG.md`
- **Why:**
  - Build frontend microphone recording control, backend STT upload integration, text input fallback, and automated unit tests.
- **Contracts affected:** none
- **Known issues / TODO:**
  - Integrate dialogue agent state machine (Task 6/8).

## 2026-09-19 — Scaffold React (Vite) App with Screen Manager & Media Fallback
- **What changed:**
  - Scaffolded React (Vite) frontend with Vitest and React Testing Library setup.
  - Implemented single-page screen state manager (`useState`) cycling through `Consent` -> `Chat` -> `Confirm` -> `Recommendations`.
  - Added consent notice and "Start" navigation button on `ConsentScreen`.
  - Implemented graceful `navigator.mediaDevices` detection setting a global `textFallbackMode` state flag without throwing exceptions.
  - Added mobile-first responsive CSS (`App.css`) with large tap targets (minimum 48px/54px).
  - Added automated test suite (`src/App.test.jsx`) using React Testing Library covering consent rendering, start navigation, and `navigator.mediaDevices` fallback mode state.
- **Files touched:**
  - `package.json`
  - `vite.config.js`
  - `index.html`
  - `.npmrc`
  - `src/main.jsx`
  - `src/App.jsx`
  - `src/App.css`
  - `src/components/ConsentScreen.jsx`
  - `src/components/ChatScreen.jsx`
  - `src/components/ConfirmScreen.jsx`
  - `src/components/RecommendationsScreen.jsx`
  - `src/setupTests.js`
  - `src/App.test.jsx`
  - `docs/CHANGELOG.md`
- **Why:**
  - Fulfill frontend scaffolding, screen-state manager, media fallback, mobile styling, and RTL test requirements.
- **Contracts affected:** none
- **Known issues / TODO:**
  - Implement Task 6/8 voice/text chat features consuming `textFallbackMode`.

## 2026-09-19 — Task-9: Source & normalize NSQF category data
- **What changed:**
  - Created `scripts/build_nsqf_categories.py` — downloads the NSDC Job Role List xlsx (604 roles, 36 sectors), groups them into 25 voice-friendly categories, and outputs `data/nsqf_categories.csv`.
  - Sector-to-category mapping merges related sectors (e.g. "Textile Sector Skill Council" + "Apparel, Made-Ups & Home Furnishing" → "Textiles & Tailoring"), normalises whitespace/casing variants, and handles all 36 source sectors.
  - Hard-failure path: download errors or unexpected file structure → clear error message naming the URL and expected columns, exit code 1. Never silently produces empty/bad CSV.
  - Warning if fewer than 15 distinct sectors found after grouping.
  - 17 new pytest tests covering grouping logic, CSV integrity (20-30 rows, no nulls, no duplicates), and mocked download failure.
- **Files touched:**
  - `scripts/build_nsqf_categories.py` (new)
  - `data/nsqf_categories.csv` (new, generated)
  - `tests/test_nsqf_categories.py` (new)
  - `requirements.txt` (added pandas, openpyxl)
- **Why:** Task-9 — provide the curated NSQF category data file that the skill mapper and recommender stages depend on.
- **Contracts affected:** Creates the `data/nsqf_categories.*` data file referenced in AI_RULES §2 and §3.4.
- **Known issues / TODO:** Category 25 ("Retail, Sports & General Services") is a catch-all for 7 small sectors; may need splitting if the voice conversation finds it too broad.

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
