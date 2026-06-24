"""Regression tests for the Toki Pona -> English parser/realizer."""

from tokipona import translate_to_english


def test_basic_transitive_sentence():
    result = translate_to_english("mi moku e kala")
    assert result.readings[0] == "I eat fish"
    assert "I drink fish" in result.readings
    assert result.note is None


def test_adjective_predicate_has_multiple_glosses():
    result = translate_to_english("sina pona")
    assert result.readings[0] == "You are good"
    assert "You are simple" in result.readings


def test_modal_predicate():
    result = translate_to_english("mi wile moku")
    assert result.readings[0] == "I want to eat"


def test_question_word():
    result = translate_to_english("sina wile e seme?")
    assert result.readings[0] == "What do you want?"


def test_coordinated_predicate():
    result = translate_to_english("mi moku e kala li moku e telo")
    assert result.readings[0] == "I eat fish, and eat water"


def test_la_context_clause():
    result = translate_to_english("tenpo pini la mi moku e kala")
    assert result.readings[0] == "Given the past, I eat fish"


def test_negated_question():
    result = translate_to_english("sina jo ala jo e soweli?")
    assert result.readings[0] == "Do you have animal?"


def test_typo_correction_reported():
    result = translate_to_english("mi monku e kala")
    assert result.readings
    assert result.note
    assert "monku" in result.note and "moku" in result.note


def test_multi_sentence_passage():
    result = translate_to_english("mi moku e kala. sina pona.")
    assert result.readings[0] == "I eat fish. You are good."


def test_no_predicate_glosses_noun_phrase():
    result = translate_to_english("tomo suli")
    assert result.readings
    assert "noun phrase" in result.note


def test_nothing_to_translate():
    result = translate_to_english("")
    assert result.readings == []
    assert result.note == "Nothing to translate."


def test_english_input_suggests_swap():
    result = translate_to_english("The quick brown fox jumps over the lazy dog.")
    assert result.readings == []
    assert "Swap directions" in result.note


def test_english_question_input_suggests_swap():
    result = translate_to_english("Is he a leader?")
    assert result.readings == []
    assert "Swap directions" in result.note
