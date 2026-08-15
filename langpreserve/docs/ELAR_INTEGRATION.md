# Archival integration (ELAR and similar repositories)

## Background

The [Endangered Languages Archive (ELAR)](https://www.elararchive.org/) and
peer repositories (PARADISEC, The Language Archive) are the standard
long-term homes for endangered-language documentation. They're built around
**CMDI/IMDI metadata** and typically ingest material either through a
researcher-facing deposit portal or, for larger partners, a negotiated batch
workflow — there isn't a universal, fully open public deposit API a
third-party tool can assume every archive exposes.

Kaimira's integration is built around that reality: it always produces a
complete, standards-shaped deposit bundle locally, and *optionally* pushes
it to a configured archive API if one is available.

## What gets generated

For a recording (or a whole language's worth of material via an export job),
`backend/app/services/export_service.py` generates:

- **`{recording_id}.eaf`** — a valid ELAN annotation document with a
  time-aligned transcription tier and, when available, a gloss tier carrying
  morpheme breakdown / gloss / free translation per segment.
- **`metadata.imdi.xml`** — session-level IMDI-style metadata: title,
  recording date, language name and Glottocode, and speaker/actor
  information (respecting each speaker's `consent_status`).
- **`{language}-lexicon.csv`** — a flat wordlist (IPA, community spelling,
  gloss, example sentence) suitable for spreadsheet review or import into
  dictionary-building tools.
- **LaTeX IGT blocks** — `gb4e`-formatted interlinear examples ready to drop
  into an academic paper's `.tex` source.

## Depositing with an archive

`backend/app/services/elar_integration.py` exposes two paths:

1. **`package_for_manual_deposit(bundle)`** (default, recommended) — builds
   an in-memory folder (`manifest.json`, `metadata.imdi.xml`, `media/...`,
   `documents/...`) that `scripts/export_elar.py` writes to disk. Zip that
   folder and upload it through the archive's own deposit portal. This is,
   in practice, still how most small documentation projects submit to ELAR —
   and it keeps Kaimira from depending on any one archive's private API
   surface.
2. **`submit_deposit(bundle)`** — if your archive (or institutional
   repository) does expose a deposit API, set `ELAR_API_BASE_URL` and
   `ELAR_API_KEY` in `.env` and this method will POST the bundle manifest
   directly. Raises a clear `ELARIntegrationError` if no API key is
   configured, so callers can fall back to the manual path automatically.

## Try it locally

```bash
# after seeding sample data
docker compose exec backend python scripts/export_elar.py e4f0a6b3-0001-4a2b-8c3d-000000000001
```

This writes a ready-to-zip deposit bundle to `export_output/<recording_id>/`.

## Consent and data sovereignty

Every `Speaker` and `Recording` carries a `consent_status`
(`pending`/`granted`/`restricted`/`withdrawn`), and every `Community` record
has a free-text `data_sovereignty_agreement` field summarizing the terms
under which a documentation project holds that community's material. The
IMDI metadata generator only includes a speaker's name when explicitly
provided by the caller — review `routers/export.py` and adapt it if your
project's agreement requires stricter anonymization by default. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for more on handling this responsibly.
