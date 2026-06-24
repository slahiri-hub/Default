"""Tests for the top-level package API: language detection and the
wrong-direction guards layered on top of the two translation engines."""

import tokipona
from tokipona.engine import detect_language, translate_to_english, translate_to_toki_pona


def test_package_exports_match_engine():
    assert tokipona.detect_language is detect_language
    assert tokipona.translate_to_english is translate_to_english
    assert tokipona.translate_to_toki_pona is translate_to_toki_pona


def test_detect_language_english():
    assert detect_language("The quick brown fox jumps over the lazy dog.") == "en"
    assert detect_language("Is he a leader?") == "en"
    assert detect_language("I love you") == "en"


def test_detect_language_toki_pona():
    assert detect_language("mi moku e kala") == "tp"
    assert detect_language("sina pona") == "tp"
    assert detect_language("jan li pona") == "tp"
    assert detect_language("mi wile moku") == "tp"


def test_translate_to_english_rejects_english_input():
    result = translate_to_english("The quick brown fox jumps over the lazy dog.")
    assert result.readings == []
    assert "Swap directions" in result.note


def test_translate_to_english_accepts_toki_pona_input():
    result = translate_to_english("mi moku e kala")
    assert result.readings[0] == "I eat fish"
    assert result.note is None


def test_translate_to_toki_pona_rejects_toki_pona_input():
    result = translate_to_toki_pona("mi moku e kala li moku e telo")
    assert result.readings == []
    assert "Swap directions" in result.note


def test_translate_to_toki_pona_accepts_english_input():
    result = translate_to_toki_pona("I eat fish.")
    assert result.readings[0] == "mi moku e kala"
    assert result.note is None


def test_mismatch_guard_does_not_misfire_on_short_toki_pona():
    # Below the word-count floor for the mismatch guard -- should pass
    # straight through rather than being second-guessed.
    result = translate_to_english("sina pona")
    assert result.readings
    assert result.note is None


def test_mismatch_guard_tolerates_proper_names_in_toki_pona():
    result = translate_to_english("jan Lisa li pona tawa mi")
    assert result.readings
    assert result.note is None
