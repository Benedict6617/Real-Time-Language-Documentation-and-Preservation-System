from app.services.grammar_analysis_service import generate_draft_igt


def test_generate_draft_igt_splits_hyphenated_words():
    result = generate_draft_igt("a-tsʼúgé-le nde")
    assert result.surface_form == "a-tsʼúgé-le nde"
    assert "a-tsʼúgé-le" in result.morpheme_breakdown
    assert result.gloss_line  # non-empty
    assert len(result.gloss_line.split()) == 2  # one gloss block per word


def test_generate_draft_igt_applies_known_prefix_gloss():
    result = generate_draft_igt("atsuge")
    assert result.gloss_line.startswith("3SG")


def test_generate_draft_igt_uses_translation_hint_when_given():
    result = generate_draft_igt("nde", free_translation_hint="he runs")
    assert result.free_translation == "he runs"


def test_generate_draft_igt_defaults_translation_placeholder():
    result = generate_draft_igt("nde")
    assert result.free_translation == "[translation needed]"
