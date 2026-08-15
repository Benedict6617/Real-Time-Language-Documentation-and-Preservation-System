"""Automatic Speech Recognition service.

Kaimira ships with a deterministic mock provider so the full pipeline can be
demoed and tested without a GPU or model weights. In production you swap
`ASR_PROVIDER` to `whisper_local` (a fine-tuned Whisper/Wav2Vec2 checkpoint
for your target language) or `custom_endpoint` (any HTTP service implementing
the same contract) — see `docs/ARCHITECTURE.md#asr-pipeline`.

Low-resource language notes
----------------------------
Endangered/low-resource languages rarely have enough transcribed audio to
train a model from scratch. The recommended production path is:
  1. Fine-tune a multilingual base model (e.g. Whisper, MMS, XLS-R) on
     whatever transcribed data exists for the target language or its family.
  2. Use `confidence` scores from this service to route low-confidence
     segments straight to the community annotation queue instead of
     surfacing them as-if-correct.
  3. Periodically retrain on newly community-corrected transcriptions
     (`TranscriptionSource.COMMUNITY_VERIFIED`) to close the loop.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

import httpx

from app.config import get_settings

settings = get_settings()


@dataclass
class ASRSegmentResult:
    start_ms: int
    end_ms: int
    text: str
    confidence: float


@dataclass
class ASRResult:
    text: str
    segments: list[ASRSegmentResult]
    model_version: str
    mean_confidence: float


class ASRServiceError(RuntimeError):
    pass


class BaseASRProvider:
    async def transcribe(
        self, audio_bytes: bytes, *, language_hint_iso: str | None = None
    ) -> ASRResult:  # pragma: no cover - interface
        raise NotImplementedError


class MockASRProvider(BaseASRProvider):
    """Deterministic, offline-safe stand-in for a real ASR model.

    Produces plausible-looking segmented output so the rest of the pipeline
    (confidence-based review routing, IGT generation, exports) can be built
    and tested end-to-end before a real model is plugged in.
    """

    _SAMPLE_TOKENS = [
        "a-tsʼúgé-le", "nde", "shéyu", "kʼóla", "tá", "medá", "hun", "sí",
    ]

    async def transcribe(
        self, audio_bytes: bytes, *, language_hint_iso: str | None = None
    ) -> ASRResult:
        if not audio_bytes:
            raise ASRServiceError("No audio data provided.")

        seed = int(hashlib.sha256(audio_bytes[:4096]).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)

        n_segments = rng.randint(3, 7)
        segments: list[ASRSegmentResult] = []
        cursor_ms = 0
        for _ in range(n_segments):
            dur = rng.randint(400, 1600)
            token_count = rng.randint(1, 3)
            words = " ".join(rng.choice(self._SAMPLE_TOKENS) for _ in range(token_count))
            confidence = round(rng.uniform(0.55, 0.97), 2)
            segments.append(
                ASRSegmentResult(
                    start_ms=cursor_ms,
                    end_ms=cursor_ms + dur,
                    text=words,
                    confidence=confidence,
                )
            )
            cursor_ms += dur + rng.randint(50, 300)

        full_text = " ".join(s.text for s in segments)
        mean_conf = round(sum(s.confidence for s in segments) / len(segments), 3)
        return ASRResult(
            text=full_text,
            segments=segments,
            model_version="mock-asr-v0 (deterministic, offline)",
            mean_confidence=mean_conf,
        )


class CustomEndpointASRProvider(BaseASRProvider):
    """Calls an external HTTP ASR service implementing Kaimira's ASR contract."""

    def __init__(self, endpoint_url: str):
        if not endpoint_url:
            raise ASRServiceError("ASR_ENDPOINT_URL must be set for custom_endpoint provider.")
        self.endpoint_url = endpoint_url

    async def transcribe(
        self, audio_bytes: bytes, *, language_hint_iso: str | None = None
    ) -> ASRResult:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                self.endpoint_url,
                files={"audio": ("recording.wav", audio_bytes, "audio/wav")},
                data={"language_hint_iso": language_hint_iso or ""},
            )
            response.raise_for_status()
            payload = response.json()

        segments = [ASRSegmentResult(**seg) for seg in payload["segments"]]
        return ASRResult(
            text=payload["text"],
            segments=segments,
            model_version=payload.get("model_version", "custom-endpoint"),
            mean_confidence=payload.get(
                "mean_confidence",
                sum(s.confidence for s in segments) / max(len(segments), 1),
            ),
        )


def get_asr_provider() -> BaseASRProvider:
    if settings.asr_provider == "mock":
        return MockASRProvider()
    if settings.asr_provider == "custom_endpoint":
        return CustomEndpointASRProvider(settings.asr_endpoint_url or "")
    if settings.asr_provider == "whisper_local":
        # Placeholder: import and wrap a locally-loaded fine-tuned model here.
        # Kept out of default requirements.txt to avoid forcing a heavy
        # torch/transformers install on deployments that use a remote ASR
        # endpoint instead.
        raise ASRServiceError(
            "whisper_local provider requires local model dependencies; "
            "see docs/ARCHITECTURE.md#swapping-in-a-real-asr-model."
        )
    raise ASRServiceError(f"Unknown ASR_PROVIDER: {settings.asr_provider}")
