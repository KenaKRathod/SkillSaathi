"""Tests for POST /tts endpoint — Task-19.

Covers:
- Valid text returns non-empty audio/mpeg
- Mocked gTTS failure returns {"audio_available": false}, not a 500
- Empty text returns HTTP 400
"""

from unittest.mock import MagicMock, patch
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestTTSHappyPath:
    """Valid text should return non-empty audio/mpeg content."""

    @patch("app.main.gTTS", create=True)
    def test_valid_text_returns_audio_mpeg(self, _mock_gtts_cls):
        """POST /tts with valid text returns audio/mpeg with non-empty body."""
        # Arrange: mock gTTS to write some fake MP3 bytes
        fake_audio = b"\xff\xfb\x90\x00" + b"\x00" * 100  # fake MP3 header + data

        mock_tts_instance = MagicMock()

        def fake_write_to_fp(fp):
            fp.write(fake_audio)

        mock_tts_instance.write_to_fp.side_effect = fake_write_to_fp
        _mock_gtts_cls.return_value = mock_tts_instance

        # We need to patch where gTTS is imported inside the endpoint
        with patch("app.main.gTTS", _mock_gtts_cls, create=True):
            # Actually, gTTS is imported inside the function via `from gtts import gTTS`
            # So we patch the gtts module
            with patch.dict("sys.modules", {"gtts": MagicMock(gTTS=_mock_gtts_cls)}):
                response = client.post(
                    "/tts",
                    json={"text": "Hello, welcome to SkillSaathi."},
                )

        assert response.status_code == 200
        assert "audio/mpeg" in response.headers.get("content-type", "")
        assert len(response.content) > 0

    def test_valid_text_returns_nonempty_audio_with_real_mock(self):
        """POST /tts with valid text using a properly mocked gTTS module."""
        fake_audio = b"\xff\xfb\x90\x00" + b"\x00" * 200

        mock_gtts_cls = MagicMock()
        mock_instance = MagicMock()

        def fake_write(fp):
            fp.write(fake_audio)

        mock_instance.write_to_fp.side_effect = fake_write
        mock_gtts_cls.return_value = mock_instance

        fake_gtts_module = MagicMock()
        fake_gtts_module.gTTS = mock_gtts_cls

        with patch.dict("sys.modules", {"gtts": fake_gtts_module}):
            response = client.post(
                "/tts",
                json={"text": "Test speech synthesis."},
            )

        assert response.status_code == 200
        assert "audio/mpeg" in response.headers.get("content-type", "")
        assert len(response.content) > 0
        assert response.content == fake_audio

    def test_hindi_text_autodetects_hi_language(self):
        """Devanagari text should automatically set lang='hi' for gTTS."""
        fake_audio = b"\xff\xfb\x90\x00" + b"\x00" * 200

        mock_gtts_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.write_to_fp.side_effect = lambda fp: fp.write(fake_audio)
        mock_gtts_cls.return_value = mock_instance

        fake_gtts_module = MagicMock()
        fake_gtts_module.gTTS = mock_gtts_cls

        with patch.dict("sys.modules", {"gtts": fake_gtts_module}):
            response = client.post(
                "/tts",
                json={"text": "नमस्ते! आपका स्वागत है।"},
            )

        assert response.status_code == 200
        assert response.content == fake_audio
        mock_gtts_cls.assert_called_once_with(
            text="नमस्ते! आपका स्वागत है।", lang="hi"
        )

    def test_explicit_lang_parameter_respected(self):
        """Explicit lang parameter overrides auto-detection."""
        fake_audio = b"\xff\xfb\x90\x00" + b"\x00" * 200

        mock_gtts_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.write_to_fp.side_effect = lambda fp: fp.write(fake_audio)
        mock_gtts_cls.return_value = mock_instance

        fake_gtts_module = MagicMock()
        fake_gtts_module.gTTS = mock_gtts_cls

        with patch.dict("sys.modules", {"gtts": fake_gtts_module}):
            response = client.post(
                "/tts",
                json={"text": "Hello", "lang": "hi"},
            )

        assert response.status_code == 200
        mock_gtts_cls.assert_called_once_with(text="Hello", lang="hi")


class TestTTSFailure:
    """When gTTS fails, return {audio_available: false} with 200, not a 500."""

    def test_gtts_failure_returns_audio_unavailable(self):
        """Mocked gTTS exception returns 200 with audio_available: false."""
        mock_gtts_cls = MagicMock(side_effect=Exception("gTTS network error"))

        fake_gtts_module = MagicMock()
        fake_gtts_module.gTTS = mock_gtts_cls

        with patch.dict("sys.modules", {"gtts": fake_gtts_module}):
            response = client.post(
                "/tts",
                json={"text": "This should fail gracefully."},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["audio_available"] is False

    def test_gtts_write_failure_returns_audio_unavailable(self):
        """If gTTS instantiates but write_to_fp fails, still return fallback."""
        mock_gtts_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.write_to_fp.side_effect = RuntimeError("Write failed")
        mock_gtts_cls.return_value = mock_instance

        fake_gtts_module = MagicMock()
        fake_gtts_module.gTTS = mock_gtts_cls

        with patch.dict("sys.modules", {"gtts": fake_gtts_module}):
            response = client.post(
                "/tts",
                json={"text": "Write failure test."},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["audio_available"] is False

    def test_gtts_failure_does_not_return_500(self):
        """Confirm that even a catastrophic gTTS failure never results in 500."""
        # Patch the import itself to raise
        fake_gtts_module = MagicMock()
        fake_gtts_module.gTTS = MagicMock(
            side_effect=ConnectionError("No internet")
        )

        with patch.dict("sys.modules", {"gtts": fake_gtts_module}):
            response = client.post(
                "/tts",
                json={"text": "Network failure test."},
            )

        assert response.status_code != 500
        assert response.status_code == 200
        assert response.json()["audio_available"] is False


class TestTTSValidation:
    """Edge cases for input validation."""

    def test_empty_text_returns_400(self):
        """Empty text string should return 400 Bad Request."""
        response = client.post("/tts", json={"text": ""})
        assert response.status_code == 400

    def test_whitespace_only_text_returns_400(self):
        """Whitespace-only text should return 400 Bad Request."""
        response = client.post("/tts", json={"text": "   "})
        assert response.status_code == 400

    def test_missing_text_field_returns_422(self):
        """Missing text field entirely should return 422 (Pydantic)."""
        response = client.post("/tts", json={})
        assert response.status_code == 422
