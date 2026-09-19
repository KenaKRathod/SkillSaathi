"""FastAPI application for voice-first skilling-recommendation agent."""

from typing import Any, Dict
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from app.config import settings
from app.stt import AudioDecodeError, STTUnavailableError, transcribe_audio

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
