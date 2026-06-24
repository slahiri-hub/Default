"""Top-level package API: language detection and the two translation
directions, dispatching to `en_to_tp`/`tp_to_en` and guarding each against
input fed in the wrong direction.
"""

from __future__ import annotations

import re

from .en_to_tp import TpResult, lemmatize, reverse_lookup
from .en_to_tp import translate_to_toki_pona as translate_to_toki_pona
from .lexicon import LEXICON, PARTICLES
from .tp_to_en import TranslationResult
from .tp_to_en import translate_to_english as _translate_to_english

_WORD_RE = re.compile(r"[A-Za-z']+")

# Below this fraction of a (long-enough) input's words being recognized Toki
# Pona vocabulary, the text is treated as not-Toki-Pona for the mismatch
# guard in `translate_to_english` -- the ported lexicon covers the standard
# ~138-word vocabulary, so genuine Toki Pona almost always scores far above
# this even when it includes proper names or rare words.
_TP_MISMATCH_THRESHOLD = 0.34
_MISMATCH_MIN_WORDS = 3


def _word_scores(text: str) -> tuple[int, int, int]:
    """Return (word_count, toki_pona_hits, english_hits) for a rough language guess."""
    words = [w.lower() for w in _WORD_RE.findall(text)]
    tp_hits = sum(1 for w in words if w in LEXICON or w in PARTICLES)
    en_hits = sum(1 for w in words if reverse_lookup(lemmatize(w)))
    return len(words), tp_hits, en_hits


def detect_language(text: str) -> str:
    """Guess whether `text` is Toki Pona ("tp") or English ("en")."""
    _total, tp_hits, en_hits = _word_scores(text)
    return "tp" if tp_hits > en_hits else "en"


def translate_to_english(text: str, max_readings: int = 12) -> TranslationResult:
    total, tp_hits, _en_hits = _word_scores(text)
    if total >= _MISMATCH_MIN_WORDS and tp_hits / total < _TP_MISMATCH_THRESHOLD:
        return TranslationResult(
            [],
            "This looks like English already. Swap directions to translate it into Toki Pona.",
        )
    return _translate_to_english(text, max_readings)


__all__ = ["detect_language", "translate_to_english", "translate_to_toki_pona"]
