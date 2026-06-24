"""Tokenization and typo correction for Toki Pona input.

Mirrors the original JS engine: proper-name capitalization is preserved,
unknown lowercase tokens are run through a QWERTY-aware typo corrector.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from .lexicon import LEXICON, PARTICLES

_PUNCT_RE = re.compile(r"[.,!?;:\"']")
_WS_RE = re.compile(r"\s+")

_WORD_LIST: list[str] | None = None


def word_list() -> list[str]:
    global _WORD_LIST
    if _WORD_LIST is None:
        _WORD_LIST = list(LEXICON.keys())
    return _WORD_LIST


def _build_qwerty_positions() -> dict[str, tuple[float, float]]:
    rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
    offsets = [0, 0.5, 1]
    pos: dict[str, tuple[float, float]] = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            pos[ch] = (r, c + offsets[r])
    return pos


QWERTY_POS = _build_qwerty_positions()


def key_distance(a: str, b: str) -> float:
    if a == b:
        return 0.0
    pa, pb = QWERTY_POS.get(a), QWERTY_POS.get(b)
    if pa is None or pb is None:
        return 3.0
    vertical_weight = 2.0
    dr = (pa[0] - pb[0]) * vertical_weight
    dc = pa[1] - pb[1]
    return math.sqrt(dr * dr + dc * dc)


def edit_distance(a: str, b: str, max_dist: int) -> int:
    """Bounded Levenshtein distance; returns max_dist+1 once exceeded."""
    la, lb = len(a), len(b)
    if abs(la - lb) > max_dist:
        return max_dist + 1
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        row_min = i
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if cur[j] < row_min:
                row_min = cur[j]
        if row_min > max_dist:
            return max_dist + 1
        prev = cur
    return prev[lb]


def weighted_distance(a: str, b: str) -> float:
    """Keyboard-weighted edit distance; tie-breaker among equal-edit-distance candidates."""
    la, lb = len(a), len(b)

    def sub_cost(x: str, y: str) -> float:
        if x == y:
            return 0.0
        return 0.2 + 0.6 * (key_distance(x, y) / 10)

    indel = 1.0
    prev = [j * indel for j in range(lb + 1)]
    for i in range(1, la + 1):
        cur = [i * indel] + [0.0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(
                prev[j] + indel,
                cur[j - 1] + indel,
                prev[j - 1] + sub_cost(a[i - 1], b[j - 1]),
            )
        prev = cur
    return prev[lb]


def correct_typo(word: str) -> str | None:
    if len(word) < 2:
        return None
    max_dist = 1 if len(word) <= 4 else 2
    best_dist = max_dist + 1
    candidates: list[str] = []
    for w in word_list():
        if abs(len(w) - len(word)) > max_dist:
            continue
        d = edit_distance(word, w, max_dist)
        if d > max_dist:
            continue
        if d < best_dist:
            best_dist = d
            candidates = [w]
        elif d == best_dist:
            candidates.append(w)
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    scored = sorted(((w, weighted_distance(word, w)) for w in candidates), key=lambda t: t[1])
    first, second = scored[0], scored[1]
    if second[1] - first[1] < 0.03:
        return None
    return first[0]


def is_proper_name(tok: str) -> bool:
    return bool(re.match(r"^[A-Z]", tok)) and tok.lower() not in LEXICON


@dataclass
class Correction:
    from_: str
    to: str


def tokenize(text: str, corrections: list[Correction] | None = None) -> list[str]:
    raw_tokens = [t for t in _WS_RE.split(_PUNCT_RE.sub(" ", text)) if t]
    out: list[str] = []
    for tok in raw_tokens:
        lower = tok.lower()
        is_cap = bool(re.match(r"^[A-Z]", tok))
        if is_cap and lower not in LEXICON:
            out.append(tok)
            continue
        if lower in LEXICON or lower in PARTICLES:
            out.append(lower)
            continue
        fix = correct_typo(lower)
        if fix and fix != lower:
            if corrections is not None:
                corrections.append(Correction(lower, fix))
            out.append(fix)
            continue
        out.append(lower)
    return out
