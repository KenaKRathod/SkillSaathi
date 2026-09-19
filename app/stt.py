"""Speech-to-Text service module using faster-whisper."""

import io
import logging
from typing import Any, Dict, Optional
import numpy as np
from faster_whisper.audio import decode_audio

from app.config import settings

logger = logging.getLogger(__name__)


class AudioDecodeError(ValueError):
    """Raised when an uploaded audio file is invalid or corrupted."""
    pass


class STTUnavailableError(RuntimeError):
    """Raised when the STT model fails to load or encounters a fatal runtime error."""
    pass


_whisper_model: Optional[Any] = None


def get_whisper_model() -> Any:
    """Retrieve or lazily initialize the singleton WhisperModel instance."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info(
                "Loading faster-whisper model: size=%s, device=%s, compute_type=%s",
                settings.whisper_model_size,
                settings.whisper_device,
                settings.whisper_compute_type,
            )
            _whisper_model = WhisperModel(
                settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
        except Exception as exc:
            logger.exception("Failed to initialize WhisperModel: %s", exc)
            raise STTUnavailableError(f"Whisper model failed to load: {exc}") from exc

    return _whisper_model


def set_whisper_model(model: Optional[Any]) -> None:
    """Set or reset the active WhisperModel instance (useful for tests and dependency injection)."""
    global _whisper_model
    _whisper_model = model


def transcribe_audio(audio_bytes: bytes, language: str = "auto") -> Dict[str, Any]:
    """Decode and transcribe audio bytes using faster-whisper.

    Fallback rules:
      - Empty bytes: returns {"text": "", "error": "no_speech_detected"}
      - Corrupted / invalid file: raises AudioDecodeError
      - Audio under 0.5s: returns {"text": "", "error": "no_speech_detected"}
      - Silent audio (amplitude < 1e-4) or empty transcription: returns {"text": "", "error": "no_speech_detected"}
      - Model loading / inference crash: raises STTUnavailableError

    Args:
        audio_bytes: Raw binary content of the audio file.
        language: Language code or "auto" for auto-detection.

    Returns:
        Dict[str, Any]: Either {"text": str, "language": str} on success,
                        or {"text": "", "error": "no_speech_detected"} on fallback.
    """
    # 1. Check for empty audio
    if not audio_bytes or len(audio_bytes) == 0:
        return {"text": "", "error": "no_speech_detected"}

    # 2. Decode audio waveform
    try:
        audio_array = decode_audio(io.BytesIO(audio_bytes))
    except Exception as exc:
        logger.warning("Audio decoding failed: %s", exc)
        raise AudioDecodeError("Invalid or corrupted audio file") from exc

    # 3. Check audio duration (sampling rate is 16000 Hz)
    sampling_rate = 16000
    duration = len(audio_array) / float(sampling_rate)
    if duration < 0.5:
        return {"text": "", "error": "no_speech_detected"}

    # 4. Check for pure silence (amplitude threshold)
    if len(audio_array) == 0 or float(np.max(np.abs(audio_array))) < 1e-4:
        return {"text": "", "error": "no_speech_detected"}

    # 5. Load model
    try:
        model = get_whisper_model()
    except STTUnavailableError:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve WhisperModel: %s", exc)
        raise STTUnavailableError(f"Whisper model unavailable: {exc}") from exc

    # 6. Run transcription
    whisper_lang = None if language == "auto" else language
    try:
        segments, info = model.transcribe(audio_array, language=whisper_lang)
        # Note: segments is a generator, so consume it inside try/except block
        text = "".join(segment.text for segment in segments).strip()
    except Exception as exc:
        logger.exception("Whisper transcription threw an error: %s", exc)
        raise STTUnavailableError(f"Whisper model error: {exc}") from exc

    # 7. If model transcribed empty text, return no_speech_detected fallback
    if not text:
        return {"text": "", "error": "no_speech_detected"}

    detected_lang = getattr(info, "language", None) or "auto"
    return {"text": text, "language": detected_lang}
