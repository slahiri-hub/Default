"""Regression tests for the English -> Toki Pona compiler."""

import pytest

from tokipona import translate_to_toki_pona

# (english, expected top reading)
BASIC_CASES = [
    ("I eat fish.", "mi moku e kala"),
    ("I want to eat fish.", "mi wile moku e kala"),
    ("She is big.", "ona li suli"),
    ("Do you want to eat fish?", "sina wile moku ala moku e kala?"),
    ("What is your name?", "nimi sina li seme?"),
    ("I do not want to sleep.", "mi wile lape ala"),
    ("She can not see the bird.", "ona li ken ala lukin e waso"),
    ("I love you.", "mi olin e sina"),
    ("Eat the food!", "o moku e moku!"),
    ("I have a big red house.", "mi jo e tomo suli loje"),
    ("I eat fish and drink water.", "mi moku e kala li moku e telo"),
    ("Mary loves John.", "Mary li olin e John"),
    ("I will go to the house.", "mi kama tawa tawa tomo"),
    ("She wants to learn Toki Pona.", "ona li wile kama sona e Toki Pona"),
    ("Why did you go?", "tenpo pini la sina tawa tan seme?"),
    ("He gave me a gift.", "tenpo pini la ona li pana e mi"),
    ("They are not friends.", "ona li jan pona ala"),
    ("I am going to sleep.", "mi kama lape"),
    ("I have eaten the food.", "tenpo pini la mi moku e moku"),
    ("What do you want?", "sina wile e seme?"),
    ("I eat fish or drink water.", "mi moku e kala anu moku e telo"),
    ("My friend is a leader.", "jan pona mi li jan lawa"),
    (
        "I went to the restaurant with my friend.",
        "tenpo pini la mi tawa tawa tomo moku kepeken jan pona mi",
    ),
    ("He is not a friend.", "ona li jan pona ala"),
    (
        "I gave the vehicle to my friend.",
        "tenpo pini la mi pana e tomo tawa tawa jan pona mi",
    ),
    ("I saw a car in the city.", "tenpo pini la mi lukin e tomo tawa lon ma tomo"),
    ("We went to the bathroom.", "tenpo pini la mi tawa tawa tomo telo"),
]

# (english, expected top reading, expected missing-vocab words)
UNKNOWN_VOCAB_CASES = [
    ("Who wants pizza?", "seme li wile e ⟨pizza?⟩?", ["pizza"]),
    ("How many cats does she have?", "ona li jo e ⟨cats?⟩ seme?", ["cats"]),
    ("I am hungry but I am tired.", "mi ⟨hungry?⟩. taso mi ⟨tired?⟩", ["hungry", "tired"]),
    ("When I eat, I am happy.", "mi moku la mi ⟨happy?⟩", ["happy"]),
    ("Where do you live?", "sina ⟨live?⟩ lon seme?", ["live"]),
    ("Is she happy?", "ona li ⟨happy?⟩ ala ⟨happy?⟩?", ["happy"]),
    ("Can you swim?", "sina ken ⟨swim?⟩ ala ⟨swim?⟩?", ["swim"]),
    ("The big dog runs.", "⟨dog?⟩ suli li ⟨runs?⟩", ["dog", "runs"]),
    ("I ate fish yesterday.", "tenpo pini la mi moku e kala", ["yesterday"]),
    ("She needs help.", "ona li wile e ⟨help?⟩", ["help"]),
    ("Do you have a dog?", "sina jo ala jo e ⟨dog?⟩?", ["dog"]),
    ("The criminal ran to the city.", "jan pakala li ⟨ran?⟩ tawa ma tomo", ["ran"]),


]


@pytest.mark.parametrize("english,expected", BASIC_CASES)
def test_basic_translation(english, expected):
    result = translate_to_toki_pona(english)
    assert result.readings[0] == expected
    assert result.note is None


@pytest.mark.parametrize("english,expected,missing", UNKNOWN_VOCAB_CASES)
def test_unknown_vocabulary_reported(english, expected, missing):
    result = translate_to_toki_pona(english)
    assert result.readings[0] == expected
    for word in missing:
        assert word in result.note


def test_multi_sentence_input():
    result = translate_to_toki_pona("I am a student. I study every day. I like school.")
    assert result.readings[0] == "mi ⟨student?⟩. mi kama sona e tenpo suno ale. mi sama tomo sona"
    assert "student" in result.note


def test_absolute_possessive_pronoun_standalone():
    # "mine"/"yours" form a complete NP -- distinct from the determiner use
    # ("my house"). This is the fix for the "Which house is yours?" bug.
    assert translate_to_toki_pona("This is mine.").readings[0] == "ni li mi"
    assert translate_to_toki_pona("The car is mine.").readings[0] == "tomo tawa li mi"
    assert translate_to_toki_pona("Which house is yours?").readings[0] == "sina tomo seme?"


def test_fronted_copula_question_with_noun_complement():
    # The copula is consumed early to find the subject in yes/no questions;
    # the complement parse must not depend on seeing it again.
    result = translate_to_toki_pona("Is he a leader?")
    assert result.readings[0] == "ona li jan lawa ala jan lawa?"


def test_fronted_copula_question_with_adjective_complement():
    result = translate_to_toki_pona("Is the house big?")
    assert result.readings[0] == "tomo li suli ala suli?"


def test_predicate_nominal_coordination():
    # "a leader" in the second conjunct continues the shared copula/subject
    # rather than starting a fresh (bogus) article-led subject.
    result = translate_to_toki_pona("She is a soldier and a leader.")
    assert result.readings[0] == "ona li jan utala li jan lawa"


def test_predicate_nominal_coordination_with_or_question():
    result = translate_to_toki_pona("Is he a leader or a soldier?")
    assert result.readings[0] == "ona li jan lawa ala jan lawa anu jan utala?"
    assert result.readings[0].endswith("?")


def test_or_coordination_preserves_trailing_punctuation():
    result = translate_to_toki_pona("I eat fish or drink water.")
    assert not result.readings[0].endswith(".")


def test_nothing_to_translate():
    result = translate_to_toki_pona("")
    assert result.readings == []
    assert result.note == "Nothing to translate."


def test_toki_pona_input_suggests_swap():
    result = translate_to_toki_pona("mi moku e kala li moku e telo")
    assert result.readings == []
    assert "Swap directions" in result.note
