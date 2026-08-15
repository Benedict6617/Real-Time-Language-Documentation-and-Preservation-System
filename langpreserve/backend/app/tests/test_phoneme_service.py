from app.services.phoneme_service import extract_phoneme_inventory, tokenize_ipa


def test_tokenize_ipa_handles_digraphs_before_single_chars():
    tokens = tokenize_ipa("tsʼúgé")
    assert tokens[0] == "tsʼ"


def test_extract_phoneme_inventory_ranks_by_frequency():
    transcripts = ["nde nde a", "a tá medá", "nde"]
    inventory = extract_phoneme_inventory(transcripts)

    assert inventory[0].frequency_rank == 1
    # 'n' from "nde" x3 should outrank single-occurrence symbols.
    top_symbols = {p.ipa_symbol for p in inventory[:2]}
    assert "n" in top_symbols or "d" in top_symbols


def test_extract_phoneme_inventory_respects_top_n():
    transcripts = ["a e i o u n d s h l"]
    inventory = extract_phoneme_inventory(transcripts, top_n=3)
    assert len(inventory) == 3


def test_extract_phoneme_inventory_empty_input():
    assert extract_phoneme_inventory([]) == []
