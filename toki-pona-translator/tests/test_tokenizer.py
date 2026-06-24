"""Tests for tokenization and QWERTY-aware typo correction."""

from tokipona.tokenizer import Correction, correct_typo, edit_distance, is_proper_name, tokenize


def test_edit_distance_basic():
    assert edit_distance("moku", "moku", 2) == 0
    assert edit_distance("moku", "monku", 2) == 1
    assert edit_distance("kala", "tomo", 1) == 2  # exceeds max_dist


def test_correct_typo_finds_close_word():
    assert correct_typo("monku") == "moku"
    assert correct_typo("pina") == "pona"


def test_correct_typo_no_match_for_known_word():
    # A word already in the lexicon needs no correction.
    assert correct_typo("moku") in (None, "moku")


def test_correct_typo_ambiguous_returns_none():
    # Too-close candidates (within 0.03 weighted distance) should not guess.
    assert correct_typo("xx") is None


def test_is_proper_name():
    assert is_proper_name("Lisa") is True
    assert is_proper_name("lisa") is False
    assert is_proper_name("Toki") is False  # capitalized but a real TP word


def test_tokenize_preserves_proper_names():
    tokens = tokenize("jan Lisa li pona")
    assert tokens == ["jan", "Lisa", "li", "pona"]


def test_tokenize_corrects_typo_and_records_correction():
    corrections: list[Correction] = []
    tokens = tokenize("mi monku e kala", corrections)
    assert tokens == ["mi", "moku", "e", "kala"]
    assert corrections == [Correction("monku", "moku")]
