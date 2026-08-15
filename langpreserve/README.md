# Kaimira — Real-Time Language Documentation & Preservation Platform

[![CI](https://img.shields.io/badge/build-passing-brightgreen)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![Node 18+](https://img.shields.io/badge/node-18%2B-green)]()

> An AI-assisted toolkit that helps field linguists and native-speaker communities record,
> transcribe, analyze, and revitalize endangered languages — even in low-connectivity
> field conditions.

Kaimira pairs an offline-first mobile recorder with a cloud/self-hosted analysis
backend so a two-person field team can capture speech, get a draft transcription and
phoneme inventory the same day, and hand community members an editable, annotated
archive instead of a pile of raw `.wav` files.

---

## Why this exists

Most of the world's ~7,000 languages are under-documented, and a large share are
endangered. Existing tooling (ELAN, FLEx, Praat) is powerful but fragmented: audio
capture, transcription, annotation, and archival export live in different apps with no
shared pipeline, and almost none of it works offline in the field or gives communities
a way to interact with their own language data. Kaimira is a small-team-sized platform
that stitches these steps into one workflow, built to be self-hosted by a documentation
project, university department, or language-revitalization nonprofit.

## Core capabilities

| Area | What it does |
|---|---|
| **Recording** | Offline-first mobile app for field capture, metadata tagging, and consent tracking; syncs when connectivity returns |
| **Transcription (ASR)** | Pluggable speech-to-text pipeline tuned for low-resource languages, with confidence scoring and human-in-the-loop correction |
| **Phoneme analysis** | Automatic phoneme inventory extraction and IPA alignment from transcribed audio |
| **Grammatical analysis** | Morpheme segmentation, interlinear gloss (IGT) generation, and part-of-speech tagging assistance |
| **Multiple orthographies** | Store and render the same lexical item in IPA, a practical community orthography, and a colonial/majority-language reference script |
| **Community annotation** | Web-based review queue so native speakers can correct transcriptions, add cultural notes, and vote on preferred spellings |
| **Speech synthesis** | Basic TTS voice-building pipeline from cleaned recordings, for revitalization materials and pronunciation guides |
| **Archival export** | One-click export to ELAN (`.eaf`), IMDI/CMDI metadata, and packaging for deposit with ELAR, PARADISEC, or a local archive |
| **Learning materials** | Auto-generated flashcards, minimal-pair drills, and printable phrasebooks from annotated recordings |

## Architecture at a glance

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

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full breakdown, and
[`docs/ELAR_INTEGRATION.md`](docs/ELAR_INTEGRATION.md) for archival export details.

## Repository layout

```
backend/     FastAPI service: recordings, transcription, phonemes, grammar, export, auth
frontend/    React web dashboard for linguists & community annotators
mobile/      React Native offline-first field recording app
data/        Realistic sample dataset (3 sample languages, seed script)
docs/        Architecture, API reference, deployment, ELAR integration, contributing
scripts/     DB seeding and archive export utilities
```

## Quick start (local development)

```bash
# 1. Clone and configure
git clone <your-fork-url> kaimira
cd kaimira
cp .env.example .env

# 2. Start the stack (Postgres, MinIO object storage, backend API)
docker compose up -d

# 3. Seed realistic sample data (3 sample languages, recordings, IGT)
docker compose exec backend python scripts/seed_db.py

# 4. Run the web dashboard
cd frontend
npm install
npm run dev
```

The API will be available at `http://localhost:8000` (interactive docs at
`http://localhost:8000/docs`), and the dashboard at `http://localhost:5173`.

For the mobile field app, see [`mobile/README.md`](mobile/README.md).

## Sample data

`data/sample_data/` ships with anonymized, realistic-but-fictional documentation data
for three sample low-resource languages (Kaska Dene-style, an Austronesian-style
language, and a West African tonal language profile) so you can explore the full
pipeline — recordings, ASR drafts, phoneme inventories, interlinear glosses, and
community annotations — without needing real community data. See
[`data/README.md`](data/README.md) for details and provenance notes.

## Status & scope

This is a self-hostable reference implementation intended for a small documentation
team (1 linguist + a handful of community annotators) rather than a multi-tenant SaaS.
The ASR, phoneme, and grammar services ship with clearly-marked interfaces so you can
swap in your own models (e.g. a fine-tuned Wav2Vec2/Whisper model for your target
language) — see `backend/app/services/`.

## Contributing

Contributions from linguists, developers, and community language workers are welcome.
Please read [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) — in particular the section
on data sovereignty and community consent before submitting any real language data in
examples or tests.

## License

MIT — see [LICENSE](LICENSE). Sample data in `data/sample_data/` is synthetic/fictional
and released under the same license; it does not represent any real speech community.
