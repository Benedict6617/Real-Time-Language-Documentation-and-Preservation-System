# Sample dataset

This folder contains a realistic-but-entirely-fictional dataset used to
demo and test the full Kaimira pipeline: languages → recordings →
transcriptions → phoneme inventory → interlinear glosses → community
annotations → learning materials.

**None of this represents a real speech community, a real endangered
language, or real individuals.** The three sample languages are fictional
composites loosely modeled on general typological patterns from three
language families (Dene/Athabaskan-style, Austronesian-style, and West
African tonal-language-style) purely to exercise different parts of the
system (ejectives and complex verb morphology; simple CV syllables and
reduplication; contrastive tone). Speaker names are anonymized to initials,
consistent with the consent-handling guidance in
[`../../docs/CONTRIBUTING.md`](../../docs/CONTRIBUTING.md).

## Files

| File | Contents |
|---|---|
| `sample_languages.json` | 3 sample languages, their communities, and orthographies |
| `sample_speakers.json` | 4 sample speaker/consultant records |
| `sample_recordings.json` | 4 sample recording sessions with field metadata |
| `sample_transcriptions.json` | Transcriptions + timed segments for each recording |
| `sample_igt.json` | Interlinear glossed text (IGT) lines for two sessions |
| `sample_phonemes.json` | Hand-curated phoneme inventory entries per language |
| `sample_annotations.json` | Example community annotations (corrections, cultural notes, flags) |

No real audio is included in this repository (media files are large binary
assets not suited to git). `scripts/seed_db.py` generates short silent
placeholder `.wav` files at seed time so the full pipeline — including
storage upload and ELAN export — can be exercised end-to-end locally.

## Loading the sample data

```bash
docker compose exec backend python scripts/seed_db.py
```

This creates the database schema (if not already present), uploads
placeholder audio to object storage, and inserts all records above via the
application's models — so the seeded data is guaranteed to match the current
schema.
