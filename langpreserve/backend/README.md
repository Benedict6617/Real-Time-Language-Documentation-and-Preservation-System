# Kaimira Backend API

FastAPI + async SQLAlchemy 2.0 backend for the Kaimira language
documentation platform. See the repository root [README](../README.md) for
the full project overview and [`docs/`](../docs/) for architecture and API
reference documentation.

## Local setup (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # edit DATABASE_URL etc. to point at your local Postgres
uvicorn app.main:app --reload
```

## Tests

```bash
pytest -v
```

Tests cover the pure-function service modules (`phoneme_service`,
`grammar_analysis_service`, `export_service`) without requiring a database —
see `app/tests/`.

## Project layout

```
app/
  main.py           FastAPI app + router registration
  config.py         Environment-driven settings
  database.py       Async SQLAlchemy engine/session
  models/           ORM models (one file per domain area)
  schemas/          Pydantic request/response schemas
  routers/          API endpoints, grouped by resource
  services/         ASR, phoneme, grammar, TTS, export, storage, auth logic
  tests/            Unit tests for service modules
alembic/            Database migrations
```
