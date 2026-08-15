# Multiple orthography support

Endangered-language documentation routinely needs to represent the same
word or utterance in more than one writing system at once:

- A **phonemic IPA transcription**, used by linguists for analysis and
  comparison across languages.
- A **practical community orthography** — often based on the majority
  regional language's alphabet with added diacritics or digraphs, adopted by
  the community itself (sometimes recently, sometimes generations ago) for
  everyday writing and school use.
- A **reference/majority-language transliteration**, useful for
  cross-referencing with older archival material or making materials legible
  to institutions unfamiliar with the practical orthography.
- Occasionally a **historical orthography** used in older missionary or
  colonial-era documentation that a project wants to cross-reference against
  new work.

## How Kaimira models this

`Orthography` (`backend/app/models/language.py`) is a per-language table:
each `Language` can have any number of orthographies, each tagged with a
`kind` (`ipa` | `practical_community` | `reference_majority` | `historical`)
and one marked `is_default` for use in the dashboard's default view.

`Transcription` and `PhonemeInventoryEntry` both carry an optional
`orthography_id` / `community_spelling` reference, so:

- A transcription can be created once in IPA (typically the ASR draft
  output) and again in the practical community orthography (typically the
  human-corrected version community annotators actually read comfortably).
- Each phoneme inventory entry stores both its IPA symbol and its
  `community_spelling`, so generated learning materials
  (`learning_materials.py`) can render flashcards and phrasebooks in the
  orthography a community's students actually use, while the underlying
  phonemic analysis stays in IPA for linguistic work.

## Adding a new orthography for a language

```bash
curl -X POST http://localhost:8000/api/v1/languages/{language_id}/orthographies \
  -H "Content-Type: application/json" \
  -d '{
    "language_id": "...",
    "name": "Elders Committee Orthography (2024 revision)",
    "kind": "practical_community",
    "is_default": true,
    "description": "Adopted at the 2024 language committee meeting; replaces the 2015 draft orthography."
  }'
```

Setting a new orthography as `is_default: true` does not delete or
invalidate the previous one — older transcriptions and materials keep their
original `orthography_id` reference, so nothing is silently rewritten when a
community updates its writing system.

## Rendering considerations

The web dashboard currently displays raw transcription/gloss text as stored
(UTF-8 throughout, so IPA and any Unicode orthography render correctly out
of the box). If your language's orthography needs a particular font for
legibility (e.g. specific diacritic stacking), add a language-specific font
stack in `frontend/src/styles.css` rather than relying on system default
fonts, which vary significantly in IPA/diacritic support across devices.
