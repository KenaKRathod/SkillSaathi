Backend tasks
Task-1 — Project scaffold & session state (Backend)

Description: FastAPI app skeleton, CORS, and the in-memory session store every other endpoint will read/write.

Prompt:

Set up a FastAPI project for a voice-first skilling-recommendation agent.

Requirements:
- app/main.py with CORS enabled for http://localhost:5173
- A GET /health endpoint returning {"status": "ok"}
- An in-memory SESSIONS dict (session_id -> dict) in app/state.py, with 
  get_session(session_id) that creates a new session if one doesn't exist
- Pydantic Settings for config (LLM API key, model name) loaded from .env

Fallback: if SESSIONS grows unbounded during a long demo, add a simple 
max-size eviction (drop oldest session) rather than crashing.

Tests (write in tests/test_health.py using pytest + httpx):
- GET /health returns 200 and {"status": "ok"}
- Calling get_session() twice with the same id returns the same dict object
- Calling get_session() with a new id creates an empty profile dict

Run the tests yourself and fix anything that fails before considering this done.

Task-2 — Speech-to-text endpoint (Backend)

Description: Turns recorded audio into text using faster-whisper.

Prompt:

Add POST /transcribe to the FastAPI app.

Requirements:
- Accepts multipart/form-data with an audio file field named "audio"
- Runs it through faster-whisper (small model, language="auto")
- Returns {"text": "...", "language": "..."}

Fallback:
- If the audio is empty, silent, or under 0.5 seconds, return 
  {"text": "", "error": "no_speech_detected"} with HTTP 200 (not a 500), 
  so the frontend can show "please try again" instead of crashing
- If the whisper model fails to load or throws, return HTTP 503 with 
  {"error": "stt_unavailable"}

Tests (pytest):
- A short real speech sample (generate one with gTTS if no sample exists) 
  transcribes to non-empty text
- A silent/empty audio file returns the no_speech_detected fallback, not an 
  exception
- An invalid/corrupted file returns a clean 4xx error, not a stack trace

Run the tests and confirm all three pass before moving on.


Task-3 — Chat schema & system prompt (Backend)

Description: Define the profile schema and persona prompt as a standalone module — no endpoint yet, just the building block Task-4 needs.

Prompt:

Create app/agent_prompt.py containing:
- PROFILE_FIELDS = ["occupation", "years_experience", "tools_used", 
  "education", "district", "wage_goal", "mobility"]
- A SYSTEM_PROMPT string: friendly field-worker persona, instructs the LLM 
  to ask exactly one missing field at a time, probe vague answers, and 
  return strict JSON: {"next_question": str|null, "extracted_fields": {...}}
- A helper function is_profile_complete(profile: dict) -> bool checking all 
  PROFILE_FIELDS are non-empty

Tests (pytest, no LLM call needed):
- is_profile_complete returns False when any field is missing
- is_profile_complete returns True when all fields are filled
- SYSTEM_PROMPT is non-empty and mentions all PROFILE_FIELDS by name
Task-4 — Consent screen + app shell (Frontend)

Description: Independent of backend — can start immediately in parallel with Task-3.

Prompt:

Scaffold a React (Vite) app with a single-page screen-state manager 
(useState, no router needed) cycling through: Consent -> Chat -> Confirm -> 
Recommendations.

Requirements:
- Consent screen: notice text + "Start" button -> moves to Chat
- App.css: mobile-first, large tap targets

Fallback:
- If navigator.mediaDevices is undefined, set a global "textFallbackMode" 
  flag in state (used later by Task-6/8) instead of crashing

Tests (React Testing Library):
- Consent screen renders and Start navigates to Chat
- Mocking mediaDevices as undefined sets textFallbackMode without throwing
Task-5 — /chat endpoint, happy path only (Backend)

Description: Wires Task-3's prompt into a real endpoint. No fallback logic yet — keep this task small.

Prompt:

Add POST /chat to app/main.py using agent_prompt.py from Task-3.

Request: {"session_id": str, "message": str}
- Append message to session state, call the LLM with SYSTEM_PROMPT + 
  conversation history, parse the JSON response, merge extracted_fields 
  into the session profile
- If is_profile_complete(profile): return {"status": "complete", "profile": {...}}
- Else: return {"status": "in_progress", "next_question": "..."}

No fallback handling yet — assume the LLM always returns valid JSON.

Tests (pytest, mock the LLM to return a fixed valid JSON string):
- First call with an empty profile returns in_progress with a next_question
- A sequence of mocked calls that fill all fields returns status:complete
Task-6 — Mic recording component (Frontend)

Description: Standalone component — uses Task-2's /transcribe endpoint, independent of Task-5.

Prompt:

Build a <MicButton onTranscript={fn}> component.

Requirements:
- Press to start MediaRecorder, press again to stop
- On stop, POST the audio blob to http://localhost:8000/transcribe
- Call onTranscript(text) with the returned text
- Show a recording indicator while active, a spinner while awaiting response

Fallback:
- If textFallbackMode is true (from Task-4), render a plain text <input> + 
  submit button instead of the mic, calling onTranscript directly with the 
  typed text
- If /transcribe returns {"error": "no_speech_detected"}, call 
  onTranscript(null) instead of empty string, so the parent can show a retry 
  prompt

Tests (mock fetch):
- Successful transcribe calls onTranscript with the returned text
- no_speech_detected response calls onTranscript with null
- textFallbackMode renders the text input instead of the mic button
Task-7 — /chat fallback & retry logic (Backend)

Description: Hardens Task-5. Small, isolated addition.

Prompt:

Modify the /chat endpoint from Task-5 to add:
- Retry the LLM call once on timeout/exception; on second failure, return a 
  scripted generic question for the next empty PROFILE_FIELD instead of 
  raising an error
- If the LLM response isn't valid JSON, try regex-extracting a JSON object; 
  if that also fails, use the same scripted-question fallback
- Track consecutive off-topic replies (extracted_fields empty 3 times in a 
  row) and inject a redirect line into the next_question: "Let's get back 
  to your work — {generic question}"

Tests (pytest, mock the LLM):
- Mocked exception on both attempts returns the scripted fallback question, 
  not a 500
- Mocked malformed JSON response is handled without crashing
- Three consecutive empty-extraction mocks trigger the redirect phrasing
Task-8 — Chat screen: wire mic + messages (Frontend)

Description: Connects Task-6's mic component into the actual chat conversation loop.

Prompt:

Build the Chat screen using <MicButton> from Task-6.

Requirements:
- On transcript received, add a user chat bubble, POST 
  {session_id, message: transcript} to /chat, add the returned 
  next_question as an assistant bubble
- When /chat returns status:"complete", pass the profile up and navigate to 
  Confirm screen

Fallback:
- onTranscript(null) (from Task-6's no_speech_detected case) shows an inline 
  "Didn't catch that — try again" message, does NOT call /chat
- A failed /chat fetch shows a Retry button that re-sends the last message

Tests (mock fetch):
- A valid transcript produces both chat bubbles
- A null transcript shows the retry-prompt without calling /chat
- A failed /chat call shows Retry, and clicking it resends the same message
Task-9 — NSQF categories dataset (Backend/Data)

Description: Pure data task — can be done by a non-coder on the team, unblocks Task-11.

Prompt:

Create nsqf_categories.csv with columns: category_name, keywords, description.
Populate 20-25 realistic rows covering: agriculture & allied, construction & 
masonry, textiles & tailoring, food processing, logistics, electrical work, 
beauty & wellness, retail, plumbing, welding, driving/transport, handicrafts, 
domestic services, IT/BPO basics, healthcare support, and similar sectors.

Each row's keywords field should have 5-8 comma-separated terms a rural 
worker might actually say (e.g. "stitching, cutting cloth, blouse, sewing 
machine" for textiles & tailoring).

Test: write a tiny pytest that loads the CSV with pandas and asserts 
20 <= len(df) <= 30, no null category_name values, and no duplicate 
category_name values.
Task-10 — Confirm screen UI (mocked data) (Frontend)

Description: Build the UI against a hardcoded fake profile first — don't wait on Task-11/12 to exist.

Prompt:

Build the Confirm screen using a hardcoded mock profile object (matching 
PROFILE_FIELDS from Task-3: occupation, years_experience, tools_used, 
education, district, wage_goal, mobility).

Requirements:
- Render each field with an inline-editable text input
- "Confirm" button (wiring to a real endpoint comes in Task-13 — for now 
  just console.log the final profile)

Fallback:
- Any field missing from the mock profile renders as "Not specified" but 
  remains editable

Tests (React Testing Library):
- All 7 fields render with correct initial values
- Editing a field updates its displayed value
- A profile object missing one field still renders "Not specified" for it
Task-11 — /map-skills endpoint, happy path (Backend)

Description: Uses Task-9's CSV. No fallback yet.

Prompt:

Add POST /map-skills to app/main.py.

- Load nsqf_categories.csv with pandas at startup
- Accept a completed profile dict
- One LLM call with structured JSON output: 
  {"primary_category": str, "secondary_category": str, 
   "evidence_quotes": [str], "confidence": float}
- Return that JSON directly (no validation/fallback yet)

Tests (pytest, mock the LLM with a fixed valid response):
- A mocked response is returned as-is with all four keys present
Task-12 — /map-skills validation & fallback (Backend)

Description: Hardens Task-11.

Prompt:

Modify /map-skills from Task-11 to add:
- Validate primary_category and secondary_category exist in the CSV's 
  category_name column; if not, pick the closest match by keyword overlap 
  and cap confidence at 0.5
- If confidence < 0.6, return {"status": "needs_clarification", 
  "question": "..."} instead of the category result
- If the LLM call fails entirely, return the same needs_clarification shape 
  with a generic fallback question

Tests (pytest, mock the LLM):
- A mocked confidence of 0.9 returns the category result unchanged
- A mocked confidence of 0.4 returns needs_clarification
- A mocked invalid category name is corrected to a real CSV value
- A mocked LLM exception returns needs_clarification, not a 500
Task-13 — Wire Confirm screen to /map-skills (Frontend)

Description: Connects Task-10's UI to Task-12's real endpoint.

Prompt:

Modify the Confirm screen from Task-10: replace the mock profile with the 
real profile passed from the Chat screen (Task-8). On "Confirm", POST the 
profile to /map-skills.

Requirements:
- On a category result, pass it forward and navigate toward Recommendations 
  (full wiring happens in Task-18)
- On needs_clarification, show the returned question as a one-off follow-up 
  text input, then re-POST with the added answer

Tests (mock fetch):
- A category-result response proceeds forward
- A needs_clarification response shows the follow-up input instead
Task-14 — Skilling programs dataset (Backend/Data)

Description: Pure data task, parallel to Task-9, unblocks Task-15.

Prompt:

Create skilling_programs.csv with columns: name, scheme, sector, nsqf_level, 
duration, cost, district_availability, min_age, max_age, min_education, 
wage_outcome.
Populate 15-20 realistic rows spanning PMKVY, DDU-GKY, NAPS apprenticeships, 
and at least one state mission scheme, across varied sectors matching 
nsqf_categories.csv's category_name values.

Test: pytest asserting 15 <= len(df) <= 20, no nulls in name/scheme/sector, 
and that every sector value has at least one matching category_name in 
nsqf_categories.csv.
Task-15 — /recommend: filtering & scoring only (Backend)

Description: Uses Task-14's CSV. Reasoning generation is deferred to Task-16.

Prompt:

Add POST /recommend to app/main.py.

- Load skilling_programs.csv with pandas at startup
- Accept mapped category + profile
- Filter by eligibility: age range, min_education, district_availability
- Score remaining rows: category_match*0.5 + eligibility_fit*0.3 + 
  wage_goal_fit*0.2
- Return top 3 rows as JSON (raw data only, no reasoning text yet)

Tests (pytest):
- A profile matching an eligible program returns it in the top 3
- A program with perfect category match + eligibility scores higher than 
  one with neither (assert on the score values directly)
Task-16 — /recommend: reasoning + fallback (Backend)

Description: Adds the LLM reasoning layer and empty-result handling on top of Task-15.

Prompt:

Modify /recommend from Task-15:
- For each of the top 3 rows, add an LLM-generated "reasoning" field that 
  only references that row's actual CSV data
- If the LLM reasoning call fails, fall back to a templated sentence: 
  "{name} is a {duration} {scheme} program matching your {sector} experience."
- If zero programs pass the eligibility filter, relax district_availability 
  first, then age range, and include {"relaxed_filters": [...]} in the response

Tests (pytest, mock the LLM):
- Mocked successful reasoning appears in the response
- Mocked LLM failure falls back to the templated sentence
- A profile matching zero programs returns relaxed results with 
  relaxed_filters populated, not an empty list
Task-17 — Recommendations screen UI (mocked data) (Frontend)

Description: Build against hardcoded fake results — don't wait on Task-16.

Prompt:

Build the Recommendations screen using a hardcoded mock array of 3 program 
objects (name, scheme, nsqf_level, duration, reasoning).

Requirements:
- Render each as a card
- Support an optional relaxed_filters note above the cards
- Support an optional audio player if an audio_url is present in mock data

Fallback:
- An empty mock array renders a "no match yet" message with a "back to Chat" 
  button

Tests (React Testing Library):
- 3 mock programs render as 3 cards
- relaxed_filters note renders when present, absent when not
- Empty array renders the no-match fallback message
Task-18 — Wire Recommendations screen to /recommend (Frontend)

Description: Final wiring — connects Task-17's UI, Task-13's confirmed category, and Task-16's real endpoint.

Prompt:

Modify the Recommendations screen from Task-17: on mount, POST the confirmed 
category + profile (passed from Task-13) to /recommend, replace the mock 
array with the real response.

Fallback:
- A failed fetch shows a Retry button
- Keep all fallback rendering from Task-17 (relaxed_filters, empty array) 
  working with real data

Tests (mock fetch):
- Successful response renders real cards
- Failed fetch shows Retry, clicking it re-sends the request
Task-19 — /tts endpoint (Backend, optional)

Description: Only start this once Task-16 and Task-18 are both confirmed working end-to-end.

Prompt:

Add POST /tts accepting {"text": str}, returns audio/mpeg via gTTS.

Fallback: if gTTS fails, return HTTP 200 {"audio_available": false} instead 
of an error.

Tests (pytest, mock gTTS):
- Valid text returns non-empty audio/mpeg
- Mocked gTTS failure returns audio_available:false, not a 500
Task-20 — Audio playback wiring (Frontend, optional)

Description: Pairs with Task-19 — skip both if time is tight.

Prompt:

Modify the Recommendations screen: after loading real results, POST the 
top result's reasoning text to /tts, render an <audio> player if 
audio_available is true.

Fallback: if audio_available is false or the field is missing, render no 
audio element at all.

Tests (mock fetch):
- audio_available:true renders an audio player
- audio_available:false or missing renders no player

Suggested parallel order: backend dev runs 3→5→7→9→11→12→14→15→16→19, frontend dev runs 4→6→8→10→13→17→18→20 — each frontend task is designed to not block on its backend counterpart being finished first (mocked data / independent components), so nobody sits idle waiting on the other track.