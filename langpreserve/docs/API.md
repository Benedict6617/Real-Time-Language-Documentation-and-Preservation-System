# API Reference

Full interactive documentation (generated from the FastAPI schema) is always
available at `/docs` (Swagger UI) and `/redoc` when the backend is running.
This page is a narrative overview of the main endpoint groups.

Base URL in local development: `http://localhost:8000`

## Auth

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/auth/register` | Create a user (`admin`, `linguist`, `community_annotator`, `viewer` roles) |
| POST | `/api/v1/auth/login` | OAuth2 password grant; returns access + refresh JWTs |
| GET | `/api/v1/auth/me` | Current user, given a bearer token |

## Languages, orthographies, phonemes

| Method | Path | Notes |
|---|---|---|
| GET/POST | `/api/v1/languages` | List / create documented languages |
| GET/PATCH | `/api/v1/languages/{id}` | Read / update a language |
| GET/POST | `/api/v1/languages/{id}/orthographies` | Manage writing systems for a language |
| GET | `/api/v1/languages/{id}/phonemes` | Current phoneme inventory |
| POST | `/api/v1/languages/{id}/phonemes/auto-detect` | Re-derive the auto-detected portion of the inventory from all transcriptions on file |

## Recordings

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/recordings?language_id=` | List recordings, optionally filtered |
| POST | `/api/v1/recordings` | Upload a recording (multipart: metadata + audio file) |
| GET | `/api/v1/recordings/{id}` | Recording detail |
| PATCH | `/api/v1/recordings/{id}/status` | Move a recording through its review lifecycle |
| POST | `/api/v1/recordings/sync` | Batch-reconcile metadata for offline-captured recordings (used by the mobile app) |

## Transcription & grammar

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/recordings/{id}/transcribe` | Run the configured ASR provider, store a draft transcription + timed segments |
| GET | `/api/v1/transcriptions/{id}` | Transcription detail, with segments |
| PATCH | `/api/v1/transcriptions/{id}` | Human/community correction; setting `is_final: true` marks it `community_verified` |
| POST | `/api/v1/grammar/analyze` | Generate draft IGT lines for every segment of a transcription |
| POST | `/api/v1/grammar/igt` | Add/override a single IGT line by hand |
| GET | `/api/v1/transcriptions/{id}/igt` | List IGT lines for a transcription |

## Community annotation

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/annotations?transcription_id=&resolved=` | List annotations, filterable |
| POST | `/api/v1/annotations` | Add a correction, cultural note, alternate spelling, translation suggestion, or review flag |
| POST | `/api/v1/annotations/{id}/upvote` | Community upvote |
| POST | `/api/v1/annotations/{id}/resolve` | Mark resolved |

## Export

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/export/jobs` | Queue an async export job (ELAN, IMDI, CMDI, ELAR package, Praat TextGrid, LaTeX IGT, CSV lexicon) |
| GET | `/api/v1/export/jobs/{id}` | Job status |
| GET | `/api/v1/export/recordings/{id}/eaf` | Synchronous single-recording ELAN `.eaf` download |
| GET | `/api/v1/export/languages/{id}/lexicon.csv` | Synchronous CSV lexicon download |
| GET | `/api/v1/export/transcriptions/{id}/latex` | Synchronous LaTeX IGT block download, ready for `gb4e` |

## Community & speakers

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/community/communities` | List speaker communities |
| POST | `/api/v1/community/speakers` | Register a speaker/consultant |
| GET | `/api/v1/community/speakers/{id}` | Speaker detail |

## Learning materials & speech synthesis

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/learning-materials/generate` | Generate a flashcard deck, minimal-pairs drill, or phrasebook |
| GET | `/api/v1/languages/{id}/learning-materials` | List generated materials for a language |
| POST | `/api/v1/tts/synthesize` | Synthesize speech audio for a piece of text |

## Authentication for write endpoints

Most read (`GET`) endpoints are open in the default configuration to make
the demo/sample data easy to explore; endpoints that create or modify data
(`recordings` upload, `annotations`, `export` jobs) require a bearer token
from `/api/v1/auth/login`, and language/orthography creation is further
restricted to `admin`/`linguist` roles. Tighten the `require_roles(...)`
dependencies in `backend/app/routers/` for a production deployment.
