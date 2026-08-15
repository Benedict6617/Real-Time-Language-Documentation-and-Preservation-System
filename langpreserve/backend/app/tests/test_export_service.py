from app.services.export_service import (
    ExportIGTLine,
    ExportRecordingBundle,
    ExportSegment,
    generate_csv_lexicon,
    generate_elan_eaf,
    generate_imdi_metadata,
    generate_latex_igt,
)


def _sample_bundle() -> ExportRecordingBundle:
    return ExportRecordingBundle(
        recording_title="Coyote and Raven narrative",
        language_name="Sample Dene Language",
        speaker_display_name="M.T. (community consultant)",
        media_filename="rec-001.wav",
        segments=[
            ExportSegment(start_ms=0, end_ms=1200, text="a-tsʼúgé-le"),
            ExportSegment(start_ms=1200, end_ms=2400, text="nde shéyu"),
        ],
        igt_lines=[
            ExportIGTLine("a-tsʼúgé-le", "a-tsʼúgé-le", "3SG-run-PST", "he ran"),
        ],
    )


def test_generate_elan_eaf_contains_time_slots_and_media_ref():
    xml_output = generate_elan_eaf(_sample_bundle())
    assert "rec-001.wav" in xml_output
    assert "TIME_SLOT" in xml_output
    assert "a-tsʼúgé-le" in xml_output


def test_generate_imdi_metadata_includes_language_and_speaker():
    xml_output = generate_imdi_metadata(
        language_name="Sample Dene Language",
        glottocode="samp1234",
        session_title="Coyote and Raven narrative",
        speaker_name="M.T.",
        recorded_date="2025-06-02",
    )
    assert "Sample Dene Language" in xml_output
    assert "samp1234" in xml_output
    assert "M.T." in xml_output


def test_generate_csv_lexicon_has_header_and_rows():
    csv_text = generate_csv_lexicon(
        [{"ipa": "a", "community_spelling": "a", "gloss": "", "example_sentence": "ama"}]
    )
    lines = csv_text.strip().splitlines()
    assert lines[0] == "ipa,community_spelling,gloss,example_sentence"
    assert len(lines) == 2


def test_generate_latex_igt_includes_gb4e_environment():
    latex = generate_latex_igt(
        [ExportIGTLine("nde", "nde", "run.PST", "he ran")]
    )
    assert "\\begin{exe}" in latex
    assert "\\trans `he ran'" in latex
