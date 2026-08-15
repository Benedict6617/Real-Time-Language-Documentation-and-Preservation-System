# Contributing

Thanks for your interest in improving Kaimira. Contributions from linguists,
developers, and community language workers are all welcome — you don't need
to be a programmer to file a useful issue about a missing workflow or an
unclear export format.

## Development setup

```bash
git clone <your-fork-url> kaimira
cd kaimira
cp .env.example .env
docker compose up -d
docker compose exec backend python scripts/seed_db.py
```

Backend tests:
```bash
cd backend
pip install -r requirements.txt
pytest
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Data sovereignty and consent — please read before submitting examples

Kaimira is built to document real, living communities' languages. If you're
contributing code, docs, or examples:

- **Never commit real community recordings, real transcriptions, or real
  speaker names/PII** to this repository, including in tests, screenshots,
  or example payloads. Use the fictional sample dataset in
  `data/sample_data/` (or extend it with more fictional examples) instead.
- If you're adapting Kaimira for a real documentation project, treat
  `Community.data_sovereignty_agreement` as more than a free-text field —
  make sure your team has an actual, explicit agreement with the community
  about who owns the data, who can access it, and under what conditions it
  can be shared or published, *before* recording begins.
- Default to the most privacy-preserving option when in doubt: restrict
  rather than share, ask again rather than assume prior consent still
  applies, and keep speaker PII (exact birthdates, full names, addresses)
  out of the system entirely where a less identifying field (birth decade,
  initials, role) will do — this is why `Speaker.birth_decade` exists
  instead of a date-of-birth field.
- Respect a community's or speaker's decision about anonymity in exports —
  don't default to including full names in generated archive metadata
  unless that's what was agreed.

## Code contributions

- Keep the ASR/phoneme/grammar/TTS "service" modules dependency-light and
  swappable — the point of the provider-interface pattern
  (`get_asr_provider()`, `get_tts_provider()`, etc.) is that a team can drop
  in their own model without forking the rest of the app. If you're adding a
  new provider, follow the existing `Base*Provider` interface.
- Add or update tests for anything in `backend/app/services/` — those
  modules are pure-function-friendly by design specifically so they're easy
  to test without a database or model weights.
- Run `pytest` (backend) and `npm run lint` (frontend) before opening a PR.
- Keep PRs focused; large refactors are easier to review as several small
  PRs.

## Reporting issues

Please include:
- What you expected vs. what happened.
- Whether this is about the backend API, web dashboard, or mobile app.
- Any relevant request/response payloads — with real language data redacted
  or replaced with sample data, per the data sovereignty note above.

## Code of conduct

Be respectful, especially in discussions that touch on specific speech
communities or endangered-language politics — these are often sensitive
topics for the people involved, even in a technical repository.
