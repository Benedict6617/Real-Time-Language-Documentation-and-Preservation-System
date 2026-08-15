"""Phoneme inventory extraction and IPA alignment.

This module derives a candidate phoneme inventory from transcribed IPA text.
In a production deployment this would typically be backed by a
forced-aligner (e.g. the Montreal Forced Aligner) plus a G2P (grapheme-to-
phoneme) model trained or adapted for the target language; here we implement
a transparent, rule-based approximation so behavior is predictable and
testable without external model weights.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# A deliberately small IPA classification table covering the symbols used in
# the bundled sample data. Extend this table (or replace with a proper IPA
# feature database such as PanPhon) for real deployments.
_IPA_CLASSIFICATION: dict[str, dict[str, str]] = {
    "a": {"phoneme_type": "vowel", "place": "central", "manner": "open"},
    "e": {"phoneme_type": "vowel", "place": "front", "manner": "mid"},
    "i": {"phoneme_type": "vowel", "place": "front", "manner": "close"},
    "o": {"phoneme_type": "vowel", "place": "back", "manner": "mid"},
    "u": {"phoneme_type": "vowel", "place": "back", "manner": "close"},
    "ə": {"phoneme_type": "vowel", "place": "central", "manner": "mid"},
    "tsʼ": {"phoneme_type": "consonant", "place": "alveolar", "manner": "ejective_affricate"},
    "kʼ": {"phoneme_type": "consonant", "place": "velar", "manner": "ejective_stop"},
    "n": {"phoneme_type": "consonant", "place": "alveolar", "manner": "nasal"},
    "d": {"phoneme_type": "consonant", "place": "alveolar", "manner": "stop", "voicing": "voiced"},
    "s": {"phoneme_type": "consonant", "place": "alveolar", "manner": "fricative", "voicing": "voiceless"},
    "h": {"phoneme_type": "consonant", "place": "glottal", "manner": "fricative", "voicing": "voiceless"},
    "l": {"phoneme_type": "consonant", "place": "alveolar", "manner": "lateral_approximant"},
    "g": {"phoneme_type": "consonant", "place": "velar", "manner": "stop", "voicing": "voiced"},
    "sh": {"phoneme_type": "consonant", "place": "postalveolar", "manner": "fricative", "voicing": "voiceless"},
    "y": {"phoneme_type": "consonant", "place": "palatal", "manner": "approximant"},
    "t": {"phoneme_type": "consonant", "place": "alveolar", "manner": "stop", "voicing": "voiceless"},
    "m": {"phoneme_type": "consonant", "place": "bilabial", "manner": "nasal"},
    "j": {"phoneme_type": "consonant", "place": "palatal", "manner": "approximant"},
}

# Longest-match-first ordering so digraphs/clusters like "tsʼ" and "kʼ" are
# matched before their single-character prefixes.
_SORTED_SYMBOLS = sorted(_IPA_CLASSIFICATION.keys(), key=len, reverse=True)


@dataclass
class ExtractedPhoneme:
    ipa_symbol: str
    phoneme_type: str
    manner: str | None
    place: str | None
    voicing: str | None
    frequency_rank: int
    example_word: str | None


def tokenize_ipa(text: str) -> list[str]:
    """Greedily tokenize an IPA-ish string into known symbols.

    Unrecognized characters are skipped rather than raising, since field
    transcriptions will always contain symbols outside any fixed table —
    those simply won't contribute to the auto-detected inventory and can be
    added to `_IPA_CLASSIFICATION` (or a per-language override table) later.
    """
    tokens: list[str] = []
    i = 0
    lowered = text.lower()
    while i < len(lowered):
        if lowered[i].isspace():
            i += 1
            continue
        matched = False
        for symbol in _SORTED_SYMBOLS:
            if lowered.startswith(symbol, i):
                tokens.append(symbol)
                i += len(symbol)
                matched = True
                break
        if not matched:
            i += 1
    return tokens


def extract_phoneme_inventory(
    transcripts: list[str], *, top_n: int | None = None
) -> list[ExtractedPhoneme]:
    """Build a frequency-ranked candidate phoneme inventory from raw transcripts."""
    counter: Counter[str] = Counter()
    example_words: dict[str, str] = {}

    for transcript in transcripts:
        for word in transcript.split():
            for symbol in tokenize_ipa(word):
                counter[symbol] += 1
                example_words.setdefault(symbol, word)

    ranked = counter.most_common(top_n)
    results: list[ExtractedPhoneme] = []
    for rank, (symbol, _count) in enumerate(ranked, start=1):
        meta = _IPA_CLASSIFICATION.get(symbol, {"phoneme_type": "consonant"})
        results.append(
            ExtractedPhoneme(
                ipa_symbol=symbol,
                phoneme_type=meta.get("phoneme_type", "consonant"),
                manner=meta.get("manner"),
                place=meta.get("place"),
                voicing=meta.get("voicing"),
                frequency_rank=rank,
                example_word=example_words.get(symbol),
            )
        )
    return results
