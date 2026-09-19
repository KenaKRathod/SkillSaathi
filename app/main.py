"""FastAPI application for voice-first skilling-recommendation agent."""

import json
from typing import Any, Dict, List
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from google import genai
from app.agent_prompt import is_profile_complete
from app.chat import call_llm, get_scripted_question
from app.config import settings
from app.state import get_session
from app.stt import AudioDecodeError, STTUnavailableError, transcribe_audio

# Load NSQF categories at startup
try:
    _nsqf_df = pd.read_csv("data/nsqf_categories.csv")
    NSQF_CSV_TEXT = _nsqf_df.to_csv(index=False)
    VALID_CATEGORIES = _nsqf_df["category_name"].dropna().tolist() if "category_name" in _nsqf_df.columns else []
except Exception:
    NSQF_CSV_TEXT = ""
    VALID_CATEGORIES = []

def find_closest_category(cat_name: str, valid_categories: List[str]) -> str:
    if not valid_categories:
        return cat_name
    cat_words = set(cat_name.lower().split())
    best_match = valid_categories[0]
    best_overlap = -1
    for vc in valid_categories:
        vc_words = set(vc.lower().split())
        overlap = len(cat_words.intersection(vc_words))
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = vc
    if best_overlap == 0:
        import difflib
        matches = difflib.get_close_matches(cat_name, valid_categories, n=1)
        if matches:
            best_match = matches[0]
    return best_match

app = FastAPI(
    title="SkillSaathi API",
    description="Voice-first skilling-recommendation agent backend",
    version="0.1.0",
)

# CORS enabled for frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, str]:
    """Root endpoint welcoming users and directing them to API documentation."""
    return {
        "message": "Welcome to SkillSaathi API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Handle browser favicon request to avoid 404 in logs."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint to verify service liveness.

    Returns:
        dict: {"status": "ok"} with HTTP status 200.
    """
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)) -> JSONResponse:
    """Transcribe speech from an uploaded audio file using faster-whisper.

    Accepts multipart/form-data with field named 'audio'.

    Returns:
        - {"text": "...", "language": "..."} on success with HTTP 200
        - {"text": "", "error": "no_speech_detected"} on empty/silent/short (<0.5s) audio with HTTP 200
        - HTTP 400 with clean detail on corrupted/invalid audio files
        - HTTP 503 with {"error": "stt_unavailable"} if model fails or throws
    """
    try:
        audio_bytes = await audio.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to read audio upload: {exc}",
        )

    try:
        result = transcribe_audio(audio_bytes, language="auto")
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
    except AudioDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except STTUnavailableError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "stt_unavailable"},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "stt_unavailable"},
        )


# ---------------------------------------------------------------------------
# POST /chat — profile-building conversational endpoint
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Incoming chat message from the client."""
    session_id: str
    message: str


@app.post("/chat")
async def chat(req: ChatRequest) -> JSONResponse:
    """Conduct a single turn of the profiling conversation.

    1. Retrieve (or create) session state for ``session_id``.
    2. Append the user message to the conversation history.
    3. Call the LLM with SYSTEM_PROMPT + history (retries once on failure;
       falls back to a scripted question if both attempts fail or the
       response is unparseable JSON).
    4. Parse the JSON response, merge ``extracted_fields`` into the profile.
    5. Track consecutive empty extractions — after 3 in a row, inject a
       redirect prefix: "Let's get back to your work — {generic question}".
    6. Return ``status: complete`` with the full profile when done,
       otherwise ``status: in_progress`` with the ``next_question``.
    """
    session = get_session(req.session_id)

    # Initialise sub-keys on first access
    profile: Dict[str, Any] = session.setdefault("profile", {})
    history: List[Dict[str, str]] = session.setdefault("history", [])

    # ---- LLM turn --------------------------------------------------------
    llm_result = call_llm(history, req.message, profile=profile)

    # Persist messages into session history
    history.append({"role": "user", "parts": [{"text": req.message}]})
    if llm_result.get("next_question"):
        history.append(
            {"role": "model", "parts": [{"text": llm_result["next_question"]}]}
        )

    # Merge any newly extracted fields
    extracted: Dict[str, Any] = llm_result.get("extracted_fields", {})
    profile.update(extracted)

    # ---- Off-topic redirect tracking -------------------------------------
    empty_streak: int = session.get("empty_streak", 0)
    if extracted:
        empty_streak = 0
    else:
        empty_streak += 1

    session["empty_streak"] = empty_streak

    # After 3 consecutive empty extractions, redirect the conversation
    if empty_streak >= 3:
        scripted = get_scripted_question(profile)
        llm_result["next_question"] = (
            f"Let's get back to your work — {scripted}"
        )
        session["empty_streak"] = 0

    # ---- Response ---------------------------------------------------------
    if is_profile_complete(profile):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "complete", "profile": profile},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "in_progress",
            "next_question": llm_result.get("next_question", ""),
        },
    )



class MapSkillsRequest(BaseModel):
    profile: Dict[str, Any]

@app.post("/map-skills")
async def map_skills(req: MapSkillsRequest) -> JSONResponse:
    """Map a completed profile to NSQF categories using LLM."""
    prompt = f"""You are an expert career counselor. Map the user's profile to the best matching NSQF categories based on the provided CSV data.

NSQF Categories CSV:
{NSQF_CSV_TEXT}

User Profile:
{json.dumps(req.profile)}

Return a JSON object strictly following this structure:
{{
  "primary_category": "Category name from CSV",
  "secondary_category": "Another category name from CSV",
  "evidence_quotes": ["quote from user profile or inference"],
  "confidence": 0.85
}}
"""

    client = genai.Client(api_key=settings.llm_api_key)
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
            },
        )
        result = json.loads(response.text)
        
        confidence = float(result.get("confidence", 0.0))
        p_cat = result.get("primary_category", "")
        s_cat = result.get("secondary_category", "")
        
        needs_correction = False
        if p_cat not in VALID_CATEGORIES:
            result["primary_category"] = find_closest_category(p_cat, VALID_CATEGORIES)
            needs_correction = True
        if s_cat not in VALID_CATEGORIES:
            result["secondary_category"] = find_closest_category(s_cat, VALID_CATEGORIES)
            needs_correction = True
            
        if needs_correction:
            confidence = min(confidence, 0.5)
            result["confidence"] = confidence
            
        if confidence < 0.6:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "needs_clarification",
                    "question": "Could you provide more specific details about your daily tasks and the tools you use?"
                }
            )
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "needs_clarification",
                "question": "Could you provide more specific details about your daily tasks and the tools you use?"
            }
        )