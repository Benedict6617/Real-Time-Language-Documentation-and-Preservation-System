"""Export generators for archival deposit and academic publication.

Supported formats:
  * ELAN (.eaf) — standard tiered annotation XML consumed by ELAN/FLEx
  * IMDI / CMDI metadata — archive-standard session metadata XML
  * CSV lexicon — flat wordlist for spreadsheet review or dictionary tools
  * LaTeX IGT — `gb4e`/`expex`-style interlinear gloss blocks for papers

These generators operate on plain dataclasses rather than ORM objects so
they can be unit-tested without a database.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


@dataclass
class ExportSegment:
    start_ms: int
    end_ms: int
    text: str


@dataclass
class ExportIGTLine:
    surface_form: str
    morpheme_breakdown: str
    gloss_line: str
    free_translation: str


@dataclass
class ExportRecordingBundle:
    recording_title: str
    language_name: str
    speaker_display_name: str | None
    media_filename: str
    segments: list[ExportSegment]
    igt_lines: list[ExportIGTLine]


def _pretty_xml(element: Element) -> str:
    rough = tostring(element, encoding="utf-8")
    return minidom.parseString(rough).toprettyxml(indent="  ")


def generate_elan_eaf(bundle: ExportRecordingBundle) -> str:
    """Generate a minimal but valid ELAN .eaf XML document."""
    root = Element("ANNOTATION_DOCUMENT", {
        "AUTHOR": "Kaimira Language Documentation Platform",
        "DATE": datetime.utcnow().isoformat(),
        "FORMAT": "3.0",
        "VERSION": "3.0",
    })

    header = SubElement(root, "HEADER", {"MEDIA_FILE": "", "TIME_UNITS": "milliseconds"})
    SubElement(header, "MEDIA_DESCRIPTOR", {
        "MEDIA_URL": bundle.media_filename,
        "MIME_TYPE": "audio/x-wav",
    })

    time_order = SubElement(root, "TIME_ORDER")
    time_slot_refs: dict[int, str] = {}
    slot_counter = 1
    for seg in bundle.segments:
        for ms in (seg.start_ms, seg.end_ms):
            if ms not in time_slot_refs:
                slot_id = f"ts{slot_counter}"
                time_slot_refs[ms] = slot_id
                SubElement(time_order, "TIME_SLOT", {
                    "TIME_SLOT_ID": slot_id, "TIME_VALUE": str(ms)
                })
                slot_counter += 1

    tier = SubElement(root, "TIER", {
        "TIER_ID": "transcription",
        "LINGUISTIC_TYPE_REF": "default-lt",
        "PARTICIPANT": bundle.speaker_display_name or "unknown",
    })
    for i, seg in enumerate(bundle.segments):
        annotation = SubElement(tier, "ANNOTATION")
        aligned = SubElement(annotation, "ALIGNABLE_ANNOTATION", {
            "ANNOTATION_ID": f"a{i}",
            "TIME_SLOT_REF1": time_slot_refs[seg.start_ms],
            "TIME_SLOT_REF2": time_slot_refs[seg.end_ms],
        })
        value = SubElement(aligned, "ANNOTATION_VALUE")
        value.text = seg.text

    if bundle.igt_lines:
        gloss_tier = SubElement(root, "TIER", {
            "TIER_ID": "gloss",
            "LINGUISTIC_TYPE_REF": "gloss-lt",
        })
        for i, igt in enumerate(bundle.igt_lines):
            annotation = SubElement(gloss_tier, "ANNOTATION")
            ref = SubElement(annotation, "REF_ANNOTATION", {"ANNOTATION_ID": f"g{i}"})
            value = SubElement(ref, "ANNOTATION_VALUE")
            value.text = f"{igt.morpheme_breakdown} | {igt.gloss_line} | '{igt.free_translation}'"

    ling_type = SubElement(root, "LINGUISTIC_TYPE", {
        "LINGUISTIC_TYPE_ID": "default-lt", "TIME_ALIGNABLE": "true",
    })
    del ling_type  # kept for structural validity; no further attrs needed

    return _pretty_xml(root)


def generate_imdi_metadata(
    *, language_name: str, glottocode: str | None, session_title: str,
    speaker_name: str | None, recorded_date: str | None,
) -> str:
    """Generate a minimal IMDI-style session metadata XML document."""
    root = Element("METATRANSCRIPT", {"Type": "SESSION"})
    session = SubElement(root, "Session")
    SubElement(session, "Title").text = session_title
    SubElement(session, "Date").text = recorded_date or ""

    lang_el = SubElement(session, "Language")
    SubElement(lang_el, "Name").text = language_name
    SubElement(lang_el, "Glottocode").text = glottocode or ""

    if speaker_name:
        actors = SubElement(session, "MDGroup")
        actor_list = SubElement(actors, "Actors")
        actor = SubElement(actor_list, "Actor")
        SubElement(actor, "Name").text = speaker_name
        SubElement(actor, "Role").text = "Speaker"

    return _pretty_xml(root)


def generate_csv_lexicon(entries: list[dict[str, str]]) -> str:
    """entries: list of {ipa, community_spelling, gloss, example_sentence}."""
    output = io.StringIO()
    fieldnames = ["ipa", "community_spelling", "gloss", "example_sentence"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for entry in entries:
        writer.writerow({k: entry.get(k, "") for k in fieldnames})
    return output.getvalue()


def generate_latex_igt(igt_lines: list[ExportIGTLine]) -> str:
    """Generate `gb4e`-style LaTeX IGT blocks suitable for academic papers."""
    blocks = []
    for igt in igt_lines:
        blocks.append(
            "\\begin{exe}\n"
            "  \\ex\n"
            "  \\gll " + igt.morpheme_breakdown + " \\\\\n"
            "  " + igt.gloss_line + " \\\\\n"
            "  \\trans `" + igt.free_translation + "'\n"
            "\\end{exe}\n"
        )
    preamble = "% Requires \\usepackage{gb4e} in your LaTeX document preamble.\n"
    return preamble + "\n".join(blocks)
