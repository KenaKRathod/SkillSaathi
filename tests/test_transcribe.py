"""Tests for POST /transcribe endpoint and faster-whisper STT integration."""

import io
import wave
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.stt as stt_module

client = TestClient(app)

SAMPLE_AUDIO_PATH = Path("tests/data/sample_speech.mp3")


@pytest.fixture(scope="session")
def real_speech_audio_bytes() -> bytes:
    """Provide a real speech audio sample.

    Loads from cached file if present, otherwise generates using gTTS.
    """
    if SAMPLE_AUDIO_PATH.exists() and SAMPLE_AUDIO_PATH.stat().st_size > 0:
        return SAMPLE_AUDIO_PATH.read_bytes()

    # Generate speech with gTTS if no sample exists
    from gtts import gTTS

    buf = io.BytesIO()
    tts = gTTS(text="Welcome to SkillSaathi, your voice career advisor.", lang="en")
    tts.write_to_fp(buf)
    audio_data = buf.getvalue()

    SAMPLE_AUDIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_AUDIO_PATH.write_bytes(audio_data)
    return audio_data


@pytest.fixture
def silent_wav_bytes() -> bytes:
    """Generate a 1-second silent WAV audio file in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00" * (16000 * 2))
    return buf.getvalue()


@pytest.fixture
def short_wav_bytes() -> bytes:
    """Generate a 0.2-second WAV audio file (<0.5s requirement) in memory."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00" * int(16000 * 2 * 0.2))
    return buf.getvalue()


def test_transcribe_real_speech(real_speech_audio_bytes: bytes):
    """Confirm a short real speech sample transcribes to non-empty text and language."""
    response = client.post(
        "/transcribe",
        files={"audio": ("speech.mp3", real_speech_audio_bytes, "audio/mpeg")},
    )
    assert response.status_code == 200, f"Unexpected response: {response.text}"
    data = response.json()
    assert "text" in data
    assert isinstance(data["text"], str)
    assert len(data["text"].strip()) > 0
    assert "language" in data
    assert data["language"] is not None
    assert "error" not in data


def test_transcribe_silent_audio(silent_wav_bytes: bytes):
    """Confirm a silent audio file returns the no_speech_detected fallback with HTTP 200."""
    response = client.post(
        "/transcribe",
        files={"audio": ("silent.wav", silent_wav_bytes, "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data == {"text": "", "error": "no_speech_detected"}


def test_transcribe_empty_audio():
    """Confirm an empty audio file returns the no_speech_detected fallback with HTTP 200."""
    response = client.post(
        "/transcribe",
        files={"audio": ("empty.wav", b"", "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data == {"text": "", "error": "no_speech_detected"}


def test_transcribe_short_audio(short_wav_bytes: bytes):
    """Confirm an audio file under 0.5 seconds returns the no_speech_detected fallback."""
    response = client.post(
        "/transcribe",
        files={"audio": ("short.wav", short_wav_bytes, "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data == {"text": "", "error": "no_speech_detected"}


def test_transcribe_invalid_corrupted_file():
    """Confirm an invalid or corrupted file returns a clean 4xx error, not a stack trace or 500."""
    corrupted_data = b"RIFF\x00\x00\x00\x00THIS_IS_CORRUPTED_GARBAGE_DATA"
    response = client.post(
        "/transcribe",
        files={"audio": ("corrupt.wav", corrupted_data, "audio/wav")},
    )
    assert 400 <= response.status_code < 500
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid or corrupted audio file" in data["detail"]


def test_transcribe_model_failure_returns_503(monkeypatch, real_speech_audio_bytes: bytes):
    """Confirm that if the Whisper model fails to load or throws, HTTP 503 is returned."""
    def mock_get_whisper_model():
        raise stt_module.STTUnavailableError("Simulated Whisper model loading crash")

    monkeypatch.setattr(stt_module, "get_whisper_model", mock_get_whisper_model)

    response = client.post(
        "/transcribe",
        files={"audio": ("speech.mp3", real_speech_audio_bytes, "audio/mpeg")},
    )
    assert response.status_code == 503
    data = response.json()
    assert data == {"error": "stt_unavailable"}


def test_transcribe_inference_exception_returns_503(monkeypatch, real_speech_audio_bytes: bytes):
    """Confirm that if the Whisper model throws during inference, HTTP 503 is returned."""
    class BrokenModel:
        def transcribe(self, *args, **kwargs):
            raise RuntimeError("Inference memory fault or compute failure")

    monkeypatch.setattr(stt_module, "get_whisper_model", lambda: BrokenModel())

    response = client.post(
        "/transcribe",
        files={"audio": ("speech.mp3", real_speech_audio_bytes, "audio/mpeg")},
    )
    assert response.status_code == 503
    data = response.json()
    assert data == {"error": "stt_unavailable"}
