"""Speech synthesis service for language revival materials.

Voice-building for a low-resource language typically means fine-tuning a
small multi-speaker TTS model (e.g. a Coqui TTS / VITS checkpoint) on
community-approved, cleanly-segmented recordings from one or more consenting
speakers. This module defines the contract Kaimira uses; the default `mock`
provider returns a synthetic silent-audio placeholder so the API and
frontend can be exercised without model weights or a GPU.
"""
from __future__ import annotations

import io
import struct
import wave
from dataclasses import dataclass

from app.config import get_settings

settings = get_settings()


@dataclass
class SynthesisResult:
    audio_bytes: bytes
    format: str
    duration_seconds: float
    provider: str


class TTSServiceError(RuntimeError):
    pass


class BaseTTSProvider:
    async def synthesize(
        self, text: str, *, voice_profile: str | None = None
    ) -> SynthesisResult:  # pragma: no cover - interface
        raise NotImplementedError


class MockTTSProvider(BaseTTSProvider):
    """Generates a valid, silent WAV file sized proportionally to input text.

    This keeps the API contract (byte stream + duration) real and testable
    without bundling model weights in this reference implementation.
    """

    async def synthesize(
        self, text: str, *, voice_profile: str | None = None
    ) -> SynthesisResult:
        if not text.strip():
            raise TTSServiceError("Cannot synthesize empty text.")

        sample_rate = 16000
        duration = max(0.6, min(len(text) * 0.06, 30.0))
        n_frames = int(sample_rate * duration)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(struct.pack("<%dh" % n_frames, *([0] * n_frames)))

        return SynthesisResult(
            audio_bytes=buffer.getvalue(),
            format="wav",
            duration_seconds=round(duration, 2),
            provider="mock-tts-v0 (silent placeholder audio)",
        )


def get_tts_provider() -> BaseTTSProvider:
    if settings.tts_provider == "mock":
        return MockTTSProvider()
    raise TTSServiceError(
        f"TTS provider '{settings.tts_provider}' requires additional local "
        "dependencies not included by default — see docs/ARCHITECTURE.md."
    )
