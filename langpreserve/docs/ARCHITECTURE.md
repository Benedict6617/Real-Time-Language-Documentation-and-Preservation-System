# Architecture

## Overview

Kaimira is split into three deployable units that share one backend API:

1. **Backend API** (`backend/`) — FastAPI service exposing recordings,
   transcription, phoneme/grammar analysis, community annotation, export,
   and revitalization-material endpoints over REST. Async SQLAlchemy 2.0
   against PostgreSQL; media stored in S3-compatible object storage
   (self-hosted MinIO by default via `docker-compose.yml`).
2. **Web dashboard** (`frontend/`) — React/Vite SPA for linguists and
   community annotators: review/correct transcriptions, run ASR and draft
   grammatical analysis, manage the annotation queue, generate learning
   materials, and trigger archival exports.
3. **Offline mobile field app** (`mobile/`) — React Native/Expo app for
   capturing recordings with zero connectivity, syncing opportunistically
   when a connection becomes available.

```
                     ┌────────────────────────┐
   Offline mobile ─▶ │   Sync Gateway (REST)   │
   recorder (RN)     └───────────┬─────────────┘
                                  │
                     ┌────────────────────────┐
                     │      FastAPI Backend     │
                     │  ┌──────────────────┐    │
                     │  │ ASR Service       │    │
                     │  │ Phoneme Service   │    │
                     │  │ Grammar Analysis  │    │
                     │  │ TTS Service       │    │
                     │  │ ELAR/Archive Adapt│    │
                     │  └──────────────────┘    │
                     └───────────┬─────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
          PostgreSQL       Object storage       Web Dashboard
        (metadata, IGT)    (audio/media)      (React, annotation UI)
```

## Data model

Core entities (see `backend/app/models/`):

- **Community** / **Speaker** — the people and groups behind the data, with
  explicit consent tracking (`ConsentStatus`) at both the speaker and
  per-recording level, and a `data_sovereignty_agreement` field on
  `Community` to record the terms under which a project holds their data.
- **Language** / **Orthography** / **PhonemeInventoryEntry** — a documented
  language, its writing systems (IPA, practical community orthography,
  reference/majority-language orthography, historical), and its phoneme
  inventory, each phoneme carrying cross-orthography spellings.
- **Recording** — one field-captured audio session with genre, location,
  consent, and sync provenance (`captured_offline`).
- **Transcription** / **TranscriptionSegment** — the text of a recording,
  timestamp-aligned at the segment level, tracked through a lifecycle
  (`asr_draft` → `human_corrected` → `community_verified`).
- **InterlinearGloss** — one IGT (interlinear glossed text) line: surface
  form, morpheme breakdown, Leipzig-style gloss, free translation, POS tags.
- **Annotation** — a community/linguist note attached to a transcription or
  IGT line (correction, cultural note, alternate spelling, translation
  suggestion, or review flag), with upvoting and resolution tracking.
- **LearningMaterial** — generated revitalization content (flashcards,
  minimal pairs, phrasebooks) derived from the above.
- **ArchiveExportJob** — tracks a packaging/export job targeting ELAN,
  IMDI/CMDI metadata, an ELAR-style archive deposit, or academic formats.

## ASR pipeline

`backend/app/services/asr_service.py` defines a small provider interface
(`BaseASRProvider.transcribe`) with three implementations selectable via
`ASR_PROVIDER`:

- `mock` (default) — deterministic, dependency-free placeholder so the full
  pipeline can be demoed/tested without a GPU or model weights.
- `custom_endpoint` — calls any HTTP service implementing the same
  multipart-audio-in / segmented-text-out contract. This is the recommended
  integration point for a real model.
- `whisper_local` — placeholder for a locally-loaded, fine-tuned checkpoint;
  intentionally left unimplemented in this reference repo to avoid forcing a
  heavy `torch`/`transformers` dependency on deployments that don't need it.

### Swapping in a real ASR model

For a genuinely low-resource language, plan on:

1. Fine-tuning a multilingual base model (Whisper, MMS, or XLS-R) on
   whatever transcribed audio exists for the language or its close
   relatives.
2. Serving it behind a small HTTP wrapper matching the `custom_endpoint`
   contract (see `CustomEndpointASRProvider` for the exact request/response
   shape), and pointing `ASR_ENDPOINT_URL` at it.
3. Using the `confidence` field this service already threads through the
   pipeline to auto-route low-confidence recordings to
   `RecordingStatus.UNDER_REVIEW` instead of surfacing unreviewed ASR output
   as if it were correct (see `routers/transcription.py`).
4. Periodically retraining on newly `community_verified` transcriptions to
   close the loop — the schema already tracks transcription provenance for
   exactly this purpose.

## Phoneme and grammar analysis

`phoneme_service.py` and `grammar_analysis_service.py` are intentionally
transparent, rule-based approximations rather than opaque ML calls — this
keeps behavior predictable, testable without model weights, and easy for a
linguist to audit and extend per-language. For production use on a specific
language, most teams will want to:

- Extend or replace the IPA classification table in `phoneme_service.py`
  with a full feature system (e.g. PanPhon) or the actual phoneme inventory
  established during initial fieldwork.
- Replace `grammar_analysis_service.py`'s heuristic morpheme splitter with a
  finite-state morphological analyzer (`foma`/`HFST`) once enough data
  exists to build one — the draft-IGT contract (`DraftIGTLine`) is stable
  regardless of what generates it.

## Speech synthesis

`tts_service.py` follows the same provider-interface pattern as ASR. The
bundled `mock` provider generates valid-but-silent audio so the API contract
is exercised without model weights; production deployments typically
fine-tune a small multi-speaker model (e.g. Coqui TTS/VITS) on
community-approved, cleanly segmented recordings.

## Archival export & ELAR integration

See [`ELAR_INTEGRATION.md`](ELAR_INTEGRATION.md) for the full picture. In
short: `export_service.py` generates format-specific documents (ELAN `.eaf`,
IMDI metadata, CSV lexicons, LaTeX IGT blocks) from plain dataclasses so they
can be unit-tested without a database, and `elar_integration.py` wraps those
into a deposit-ready bundle — either for direct API submission (if your
target archive exposes one) or for manual upload through an archive's own
web portal, which remains the most common workflow for small projects.

## Multiple orthographies

A `Language` can have any number of `Orthography` records (`kind`: `ipa`,
`practical_community`, `reference_majority`, `historical`). Transcriptions
and phoneme inventory entries reference the orthography they were recorded
in, so the same lexical content can be rendered in IPA for linguistic
analysis, a practical community spelling for revitalization materials, and a
majority-language reference spelling for cross-reference — without
duplicating the underlying recording or analysis.

## Offline-first mobile sync

The mobile app never blocks on network access (see `mobile/README.md`).
`Recording.captured_offline` and the batch `/api/v1/recordings/sync`
endpoint exist specifically to reconcile metadata created without
connectivity, keeping the sync payload small so it succeeds even on a weak
signal.
