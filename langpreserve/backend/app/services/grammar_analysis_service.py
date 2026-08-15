"""Draft grammatical analysis: morpheme segmentation and interlinear glossing.

Produces a *draft* IGT (interlinear glossed text) line per surface word, which
linguists and community annotators then correct through the annotation
workflow (`app/routers/annotations.py`). This module intentionally does not
try to be a full morphological analyzer — for real deployments, plug in a
finite-state morphological analyzer (e.g. built with `foma`/`HFST`) trained
on the target language's grammar, and use this module's output shape as the
contract the rest of the system expects.
"""
from __future__ import annotations

from dataclasses import dataclass

# A tiny illustrative gloss table. Keyed by a naive heuristic (morpheme
# position + shape) rather than real morphology, to keep the mock pipeline
# dependency-free. Replace with a real morphological parser per language.
_COMMON_PREFIX_GLOSSES = {
    "a": "3SG",
    "ni": "1SG",
    "hu": "NEG",
}
_COMMON_SUFFIX_GLOSSES = {
    "le": "PST",
    "ba": "FUT",
    "ge": "IPFV",
}


@dataclass
class DraftIGTLine:
    surface_form: str
    morpheme_breakdown: str
    gloss_line: str
    free_translation: str
    pos_tags: str


def _split_morphemes(word: str) -> list[str]:
    """Naive morpheme splitter: breaks on hyphens if already marked, else
    applies a light heuristic looking for known prefix/suffix shapes.
    """
    if "-" in word:
        return word.split("-")

    morphemes = [word]
    for prefix in _COMMON_PREFIX_GLOSSES:
        if word.startswith(prefix) and len(word) > len(prefix) + 1:
            morphemes = [prefix, word[len(prefix):]]
            break
    last = morphemes[-1]
    for suffix in _COMMON_SUFFIX_GLOSSES:
        if last.endswith(suffix) and len(last) > len(suffix) + 1:
            morphemes = morphemes[:-1] + [last[: -len(suffix)], suffix]
            break
    return morphemes


def _gloss_morpheme(morpheme: str, position: int, total: int) -> str:
    if position == 0 and morpheme in _COMMON_PREFIX_GLOSSES:
        return _COMMON_PREFIX_GLOSSES[morpheme]
    if position == total - 1 and morpheme in _COMMON_SUFFIX_GLOSSES:
        return _COMMON_SUFFIX_GLOSSES[morpheme]
    return morpheme.upper() if len(morpheme) <= 2 else "ROOT"


def generate_draft_igt(surface_text: str, *, free_translation_hint: str = "") -> DraftIGTLine:
    """Generate one draft IGT line for a single transcribed utterance."""
    words = surface_text.strip().split()
    all_morphemes: list[str] = []
    all_glosses: list[str] = []
    pos_tags: list[str] = []

    for word in words:
        morphemes = _split_morphemes(word)
        all_morphemes.append("-".join(morphemes))
        glosses = [
            _gloss_morpheme(m, i, len(morphemes)) for i, m in enumerate(morphemes)
        ]
        all_glosses.append("-".join(glosses))
        pos_tags.append("V" if len(morphemes) > 1 else "N")

    return DraftIGTLine(
        surface_form=surface_text.strip(),
        morpheme_breakdown=" ".join(all_morphemes),
        gloss_line=" ".join(all_glosses),
        free_translation=free_translation_hint or "[translation needed]",
        pos_tags=" ".join(pos_tags),
    )
