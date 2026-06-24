"""Deep, clause-based English -> Toki Pona compiler.

Unlike the original engine's single-slot, bag-of-words heuristic (one
subject/verb/object/adjective guessed by scanning word order), this module
does real clause-level work: subordinate/coordinate clause splitting, NP/PP
structure, modal (pre-verb) chains, negation scope, tense/aspect, and yes/no
& wh-question formation. Vocabulary coverage is still limited to the ~150
word Toki Pona lexicon, so unknown English words surface as bracketed
glosses rather than failing outright.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from .lexicon import COMPOUNDS, LEXICON

UNKNOWN = "⟨{}?⟩"

# ---------------------------------------------------------------------------
# Reverse lexicon index: English word/phrase -> Toki Pona candidates.
# ---------------------------------------------------------------------------

_REVERSE_ROLES = ("n", "v", "vt", "mod", "prep", "number", "interj", "pre-verb")


@dataclass(frozen=True)
class Hit:
    tp: str
    role: str


_REVERSE: dict[str, list[Hit]] | None = None
_REVERSE_PHRASES: dict[str, list[Hit]] | None = None


def _build_reverse() -> None:
    global _REVERSE, _REVERSE_PHRASES
    single: dict[str, list[Hit]] = {}
    phrases: dict[str, list[Hit]] = {}

    def add(tp: str, role: str, glosses: list[str]) -> None:
        for en in glosses:
            key = en.lower()
            bucket = phrases if " " in key else single
            bucket.setdefault(key, []).append(Hit(tp, role))

    for tp, entry in LEXICON.items():
        for role in _REVERSE_ROLES:
            senses = entry.get(role)
            if senses:
                add(tp, role, senses)
    for tp, entry in COMPOUNDS.items():
        for role, senses in entry.items():
            add(tp, role, senses)

    _REVERSE = single
    _REVERSE_PHRASES = phrases


def reverse_lookup(word: str) -> list[Hit]:
    if _REVERSE is None:
        _build_reverse()
    return _REVERSE.get(word.lower(), [])


def reverse_phrases() -> dict[str, list[Hit]]:
    if _REVERSE_PHRASES is None:
        _build_reverse()
    return _REVERSE_PHRASES


def best_hit(word: str, *roles: str) -> Hit | None:
    """First reverse-lookup hit matching one of `roles`, in priority order."""
    hits = reverse_lookup(word)
    for role in roles:
        for h in hits:
            if h.role == role:
                return h
    return hits[0] if hits else None


def has_sense(word: str, role: str) -> bool:
    """True iff `word` has a reverse-lookup hit tagged with exactly `role`.

    Unlike `best_hit`, this never falls back to an unrelated sense, so it is
    safe to use as a yes/no test when deciding whether a token plausibly
    fills a given grammatical slot (e.g. "is this an adjective?").
    """
    return any(h.role == role for h in reverse_lookup(word))


def _looks_like_noun_candidate(word: str) -> bool:
    """True if `word` could plausibly head a noun phrase.

    Words with no lexicon entry at all are allowed through (they surface as
    a bracketed unknown gloss), but words the lexicon only knows as a verb,
    pre-verb, or other non-noun sense are rejected so they don't get
    swallowed as a bogus NP head (e.g. "eat" in "eat the food").
    """
    hits = reverse_lookup(word)
    return not hits or any(h.role == "n" for h in hits)


def gloss(word: str, *roles: str) -> str:
    hit = best_hit(word, *roles)
    return hit.tp if hit else UNKNOWN.format(word)


# ---------------------------------------------------------------------------
# Contraction expansion (applied to raw text before tokenizing).
# ---------------------------------------------------------------------------

_CONTRACTIONS = {
    "won't": "will not", "can't": "can not", "cannot": "can not",
    "shan't": "shall not",
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "hadn't": "had not",
    "wouldn't": "would not", "shouldn't": "should not", "couldn't": "could not",
    "mustn't": "must not", "mightn't": "might not", "needn't": "need not",
    "i'm": "i am", "you're": "you are", "we're": "we are", "they're": "they are",
    "it's": "it is", "he's": "he is", "she's": "she is", "that's": "that is",
    "what's": "what is", "who's": "who is", "where's": "where is",
    "i've": "i have", "you've": "you have", "we've": "we have", "they've": "they have",
    "i'll": "i will", "you'll": "you will", "we'll": "we will", "they'll": "they will",
    "he'll": "he will", "she'll": "she will", "it'll": "it will",
    "i'd": "i would", "you'd": "you would", "we'd": "we would", "they'd": "they would",
    "he'd": "he would", "she'd": "she would",
    "let's": "let us",
}
_CONTRACTION_RE = re.compile(
    "|".join(re.escape(k) for k in sorted(_CONTRACTIONS, key=len, reverse=True)),
    re.IGNORECASE,
)


def expand_contractions(text: str) -> str:
    def repl(m: re.Match) -> str:
        return _CONTRACTIONS[m.group(0).lower()]

    return _CONTRACTION_RE.sub(repl, text)


# ---------------------------------------------------------------------------
# Closed-class word tables.
# ---------------------------------------------------------------------------

PRONOUN_TP = {
    "i": "mi", "me": "mi", "we": "mi", "us": "mi",
    "you": "sina",
    "he": "ona", "she": "ona", "it": "ona", "they": "ona",
    "him": "ona", "her": "ona", "them": "ona",
    "this": "ni", "that": "ni", "these": "ni", "those": "ni",
}

POSSESSIVE_TP = {
    "my": "mi", "our": "mi", "your": "sina",
    "his": "ona", "her": "ona", "its": "ona", "their": "ona",
}

# Standalone/absolute possessive pronouns ("this is mine", "which house is
# yours?") form a complete NP on their own, with no following head noun
# expected -- unlike POSSESSIVE_TP's determiner forms ("my house").
ABSOLUTE_POSSESSIVE_TP = {
    "mine": "mi", "yours": "sina", "his": "ona", "hers": "ona",
    "ours": "mi", "theirs": "ona",
}

ARTICLES = frozenset(["a", "an", "the", "some", "any"])

PREP_MAP = {
    "to": "tawa", "toward": "tawa", "towards": "tawa", "for": "tawa",
    "from": "tan", "because of": "tan",
    "in": "lon", "at": "lon", "on": "lon", "inside": "insa", "within": "insa",
    "with": "kepeken", "using": "kepeken", "via": "kepeken",
    "like": "sama", "as": "sama",
    "beside": "poka", "near": "poka", "by": "poka", "next to": "poka",
}

NEGATORS = frozenset(["not", "never", "no"])

COPULA_WORDS = frozenset(["is", "are", "am", "was", "were", "be", "being", "been"])
COPULA_PAST = frozenset(["was", "were"])

AUX_DO = frozenset(["do", "does", "did"])
AUX_DO_PAST = frozenset(["did"])

AUX_PERFECT = frozenset(["have", "has", "had"])
AUX_PERFECT_PAST = frozenset(["had"])

# True modals never take a direct NP object themselves, so they are always
# safe to read as a fronted-aux/pre-verb trigger regardless of what follows.
TRUE_MODAL_WORDS = {
    "must": "wile", "should": "wile", "shall": "wile",
    "can": "ken", "could": "ken", "may": "ken", "might": "ken",
    "will": "kama", "would": "kama",
}

# Catenative verbs (want/need/keep/...) can ALSO take a bare direct object
# ("I want pizza"), so they must only be treated as a pre-verb/fronted-aux
# trigger when the following word is itself verb-like. See
# `_single_modal_match` / `_is_fronted_aux_word`.
CATENATIVE_WORDS = {
    "want": "wile", "wants": "wile", "wanted": "wile",
    "need": "wile", "needs": "wile", "needed": "wile",
    "become": "kama", "becomes": "kama", "became": "kama",
    "start": "kama", "starts": "kama", "started": "kama",
    "begin": "kama", "begins": "kama", "began": "kama",
    "keep": "awen", "keeps": "awen", "kept": "awen",
    "continue": "awen", "continues": "awen", "continued": "awen",
    "try": "lukin", "tries": "lukin", "tried": "lukin",
    "seek": "alasa", "seeks": "alasa", "sought": "alasa",
    "learn": "kama sona", "learns": "kama sona", "learned": "kama sona", "learnt": "kama sona",
}

# Single-word modal/aspect triggers -> resolved Toki Pona pre-verb token(s).
MODAL_WORDS = {**TRUE_MODAL_WORDS, **CATENATIVE_WORDS}

# Multi-word modal phrases, longest-first so greedy matching prefers them.
MODAL_PHRASES = sorted(
    [
        ("be able to", "ken"), ("being able to", "ken"), ("been able to", "ken"),
        ("be going to", "kama"),
        ("have to", "wile"), ("has to", "wile"), ("had to", "wile"),
        ("used to", "kama"),
        ("want to", "wile"), ("wants to", "wile"), ("wanted to", "wile"),
        ("need to", "wile"), ("needs to", "wile"), ("needed to", "wile"),
        ("try to", "lukin"), ("tries to", "lukin"), ("tried to", "lukin"), ("trying to", "lukin"),
        ("seek to", "alasa"), ("seeks to", "alasa"), ("sought to", "alasa"),
        ("keep on", "awen"),
        ("continue to", "awen"), ("continues to", "awen"), ("continued to", "awen"),
        ("start to", "kama"), ("starts to", "kama"), ("started to", "kama"),
        ("begin to", "kama"), ("begins to", "kama"), ("began to", "kama"),
        ("learn to", "kama sona"), ("learns to", "kama sona"),
        ("learned to", "kama sona"), ("learnt to", "kama sona"),
        ("know how to", "sona"), ("knows how to", "sona"), ("knew how to", "sona"),
    ],
    key=lambda t: -len(t[0].split()),
)

CONJUNCTIONS = frozenset(["and", "but", "or"])

SUBORDINATORS = {
    "when": "la", "whenever": "la", "if": "la", "while": "la", "unless": "la",
    "because": "tan", "since": "tan", "as": "tan",
    "before": "la", "after": "la",
    "although": "taso", "though": "taso", "even though": "taso",
}

WH_WORDS = frozenset(["who", "what", "when", "where", "why", "how", "which", "whose"])

INTENSIFIERS = {
    "very": "mute", "extremely": "mute", "so": "mute", "quite": "mute",
    "really": "a", "truly": "a", "indeed": "kin", "also": "kin", "too": "kin",
}

# Number words -> Toki Pona numeral built from the classic wan/tu/luka system.
NUMBER_WORDS = {
    "zero": "ala", "one": "wan", "two": "tu", "three": "tu wan", "four": "tu tu",
    "five": "luka", "six": "luka wan", "seven": "luka tu", "eight": "luka tu wan",
    "nine": "luka tu tu", "ten": "luka luka",
    "many": "mute", "several": "mute", "lots": "mute", "much": "mute",
    "few": "lili", "little": "lili",
    "all": "ale", "every": "ale", "each": "ale",
}

# ---------------------------------------------------------------------------
# English morphology: irregular verbs/nouns and a regular-suffix lemmatizer.
# ---------------------------------------------------------------------------

# base -> (3sg present, past, past participle, gerund)
_IRREGULAR_VERBS = {
    "be": ("is", "was", "been", "being"),
    "have": ("has", "had", "had", "having"),
    "do": ("does", "did", "done", "doing"),
    "go": ("goes", "went", "gone", "going"),
    "get": ("gets", "got", "gotten", "getting"),
    "make": ("makes", "made", "made", "making"),
    "know": ("knows", "knew", "known", "knowing"),
    "see": ("sees", "saw", "seen", "seeing"),
    "give": ("gives", "gave", "given", "giving"),
    "take": ("takes", "took", "taken", "taking"),
    "come": ("comes", "came", "come", "coming"),
    "say": ("says", "said", "said", "saying"),
    "eat": ("eats", "ate", "eaten", "eating"),
    "drink": ("drinks", "drank", "drunk", "drinking"),
    "build": ("builds", "built", "built", "building"),
    "buy": ("buys", "bought", "bought", "buying"),
    "sell": ("sells", "sold", "sold", "selling"),
    "think": ("thinks", "thought", "thought", "thinking"),
    "feel": ("feels", "felt", "felt", "feeling"),
    "leave": ("leaves", "left", "left", "leaving"),
    "lead": ("leads", "led", "led", "leading"),
    "fight": ("fights", "fought", "fought", "fighting"),
    "find": ("finds", "found", "found", "finding"),
    "grow": ("grows", "grew", "grown", "growing"),
    "begin": ("begins", "began", "begun", "beginning"),
    "break": ("breaks", "broke", "broken", "breaking"),
    "speak": ("speaks", "spoke", "spoken", "speaking"),
    "write": ("writes", "wrote", "written", "writing"),
    "die": ("dies", "died", "died", "dying"),
}

_IRREGULAR_LOOKUP: dict[str, tuple[str, str]] = {}
for _base, _forms in _IRREGULAR_VERBS.items():
    for _form in _forms:
        _IRREGULAR_LOOKUP[_form] = (_base, _form)
    _IRREGULAR_LOOKUP[_base] = (_base, _base)

_IRREGULAR_PLURAL_NOUNS = {
    "people": "person", "men": "man", "women": "woman", "children": "child",
    "feet": "foot", "teeth": "tooth", "mice": "mouse",
}


def _strip_e_suffix(base: str, suffix: str) -> list[str]:
    """Candidate stems for `base+suffix` given English spelling rules."""
    candidates = [base]
    if base.endswith("e"):
        candidates.append(base[:-1])
    else:
        candidates.append(base + "e")
    if len(base) > 2 and base[-1] == base[-2] and base[-1] not in "aeiou":
        candidates.append(base[:-1])
    return candidates


def lemmatize(word: str) -> str:
    """Best-effort reduction to a form likely present in the reverse index."""
    w = word.lower()
    if reverse_lookup(w):
        return w
    if w in _IRREGULAR_LOOKUP:
        base = _IRREGULAR_LOOKUP[w][0]
        if reverse_lookup(base):
            return base
    if w in _IRREGULAR_PLURAL_NOUNS:
        base = _IRREGULAR_PLURAL_NOUNS[w]
        if reverse_lookup(base):
            return base
    for suf in ("ies", "es", "ing", "ed", "s"):
        if w.endswith(suf) and len(w) > len(suf) + 1:
            stem = w[: -len(suf)]
            if suf == "ies":
                stem += "y"
            for cand in _strip_e_suffix(stem, suf):
                if reverse_lookup(cand):
                    return cand
    return w


def verb_tense(word: str) -> str:
    """'past' | 'present' for a bare (non-auxiliary-supported) verb form."""
    w = word.lower()
    if w in _IRREGULAR_LOOKUP:
        base, form = _IRREGULAR_LOOKUP[w]
        forms = _IRREGULAR_VERBS.get(base)
        if forms and form == forms[1]:
            return "past"
        return "present"
    if w.endswith("ed"):
        return "past"
    return "present"


def is_plural_noun(word: str) -> bool:
    w = word.lower()
    if w in _IRREGULAR_PLURAL_NOUNS:
        return True
    return w.endswith("s") and not w.endswith("ss") and lemmatize(w) != w


# ---------------------------------------------------------------------------
# Tokenization.
# ---------------------------------------------------------------------------

_PUNCT_RE = re.compile(r"[,;:\"]")
_WS_RE = re.compile(r"\s+")
_SENT_SPLIT_RE = re.compile(r"[.!?]+")
_WH_HOW_MANY_RE = re.compile(r"^how (many|much)$")


@dataclass
class Tok:
    text: str       # lowercased form used for grammar lookups
    raw: str        # original surface form (case preserved)
    is_proper: bool # capitalized & not a recognized closed/open-class word


def tokenize_en(text: str) -> list[Tok]:
    cleaned = _PUNCT_RE.sub(" ", text)
    raw_words = [w for w in _WS_RE.split(cleaned) if w]
    out: list[Tok] = []
    for idx, raw in enumerate(raw_words):
        lower = raw.lower()
        known = bool(
            lower in PRONOUN_TP or lower in POSSESSIVE_TP or lower in ABSOLUTE_POSSESSIVE_TP
            or lower in ARTICLES
            or lower in MODAL_WORDS or lower in CONJUNCTIONS or lower in SUBORDINATORS
            or lower in WH_WORDS or lower in NEGATORS or lower in COPULA_WORDS
            or lower in AUX_DO or lower in AUX_PERFECT or lower in INTENSIFIERS
            or lower in NUMBER_WORDS or lower in PREP_MAP or reverse_lookup(lemmatize(lower))
        )
        # A capitalized word unknown to the lexicon is treated as a proper
        # name even at sentence-start ("Mary loves John."): ordinary English
        # sentence-initial capitalization only affects known closed/open
        # class words, which `known` already excludes.
        is_proper = raw[:1].isupper() and not known
        out.append(Tok(lower, raw, is_proper))
    return out


def segment_sentences_en(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]


# ---------------------------------------------------------------------------
# Noun-phrase parsing.
# ---------------------------------------------------------------------------

@dataclass
class NP:
    pronoun: str | None = None       # resolved TP pronoun token ("mi"/"sina"/"ona"/"ni")
    possessive: str | None = None    # resolved TP possessive mod token
    number: str | None = None        # resolved TP numeral/quantity token
    adjectives: list[str] = field(default_factory=list)  # english lemmas
    intensifier: str | None = None   # resolved TP intensifier applying to the last adjective
    head: str | None = None          # english lemma, or a literal TP phrase from compound match
    head_is_tp: bool = False         # True if `head` is already a resolved TP phrase
    proper: str | None = None        # proper-name surface form, used verbatim
    plural: bool = False
    is_wh: bool = False              # whole NP was a bare wh-word (who/what)
    wh_word: str | None = None


def _phrase_match(tokens: list[Tok], i: int, role: str) -> tuple[Hit, int] | None:
    phrases = reverse_phrases()
    words = [t.text for t in tokens]
    max_len = min(4, len(words) - i)
    for length in range(max_len, 1, -1):
        key = " ".join(words[i : i + length])
        hits = phrases.get(key)
        if hits:
            for h in hits:
                if h.role == role:
                    return h, i + length
    return None


def parse_np(tokens: list[Tok], i: int, stop: frozenset[str]) -> tuple[NP, int] | None:
    n = len(tokens)
    # WH_WORDS sit inside `stop` (so ordinary NP scans halt at a wh-word),
    # but wh-words are also valid NPs in their own right ("who", "which
    # cat", "how many cats") via the dedicated branches just below, so they
    # must not be rejected by this generic guard.
    if i >= n or (tokens[i].text in stop and tokens[i].text not in WH_WORDS):
        return None

    np = NP()

    # Bare wh-word subject/object ("who", "what").
    if tokens[i].text in ("who", "what") and (i + 1 >= n or tokens[i + 1].text in stop or tokens[i + 1].text in CONJUNCTIONS):
        np.is_wh = True
        np.wh_word = tokens[i].text
        np.head = "seme"
        np.head_is_tp = True
        return np, i + 1

    # "how many/how much X"
    if i + 1 < n and _WH_HOW_MANY_RE.match(f"{tokens[i].text} {tokens[i+1].text}"):
        np.is_wh = True
        np.wh_word = "how many"
        i += 2
    # "which X" / "whose X"
    elif tokens[i].text in ("which", "whose"):
        np.is_wh = True
        np.wh_word = tokens[i].text
        i += 1

    # Proper name run (consecutive capitalized unknown tokens).
    if i < n and tokens[i].is_proper:
        names = []
        while i < n and tokens[i].is_proper:
            names.append(tokens[i].raw)
            i += 1
        np.proper = " ".join(names)
        return np, i

    # Pronoun (no further modification expected).
    if i < n and tokens[i].text in PRONOUN_TP and not np.is_wh:
        np.pronoun = PRONOUN_TP[tokens[i].text]
        i += 1
        return np, i

    # Absolute possessive pronoun ("yours", "his", ...) -- only when it isn't
    # itself a determiner in front of a head noun ("his house"), which the
    # lookahead distinguishes from the standalone use ("it is his").
    if (
        i < n
        and tokens[i].text in ABSOLUTE_POSSESSIVE_TP
        and not np.is_wh
        and (i + 1 >= n or tokens[i + 1].text in stop or tokens[i + 1].text in CONJUNCTIONS)
    ):
        np.possessive = ABSOLUTE_POSSESSIVE_TP[tokens[i].text]
        i += 1
        return np, i

    # Determiner: article / possessive.
    if i < n and tokens[i].text in ARTICLES:
        i += 1
    elif i < n and tokens[i].text in POSSESSIVE_TP:
        np.possessive = POSSESSIVE_TP[tokens[i].text]
        i += 1

    # Try a greedy multi-word compound match for the head (e.g. "small animal").
    m = _phrase_match(tokens, i, "n")
    if m:
        hit, i = m
        np.head = hit.tp
        np.head_is_tp = True
        if np.is_wh:
            np.adjectives.append("seme")
        return np, i

    # Number / quantity word.
    if i < n and tokens[i].text in NUMBER_WORDS and not np.is_wh:
        np.number = NUMBER_WORDS[tokens[i].text]
        i += 1

    # Adjective run (each may be preceded by an intensifier: "very big house").
    while i < n:
        tok = tokens[i].text
        if tok in stop or tok in CONJUNCTIONS:
            break
        pending_intensifier = None
        if tok in INTENSIFIERS and i + 1 < n and tokens[i + 1].text not in stop:
            pending_intensifier = INTENSIFIERS[tok]
            tok_idx = i + 1
        else:
            tok_idx = i
        lemma = lemmatize(tokens[tok_idx].text)
        if not has_sense(lemma, "mod"):
            break
        # Only consume as a modifier if something still follows for the head.
        if tok_idx + 1 >= n or tokens[tok_idx + 1].text in stop or tokens[tok_idx + 1].text in CONJUNCTIONS:
            break
        np.adjectives.append(lemma)
        if pending_intensifier:
            np.intensifier = pending_intensifier
        i = tok_idx + 1

    if (
        i < n
        and tokens[i].text not in stop
        and tokens[i].text not in CONJUNCTIONS
        and tokens[i].text not in ARTICLES
    ):
        head_lemma = lemmatize(tokens[i].text)
        if _looks_like_noun_candidate(head_lemma):
            np.head = head_lemma
            np.plural = is_plural_noun(tokens[i].text)
            i += 1

    if np.is_wh and np.wh_word in ("which", "whose", "how many"):
        np.adjectives.append("seme")

    if np.head is None and not np.adjectives and np.possessive is None and np.number is None:
        return None
    return np, i


def realize_np(np: NP) -> str:
    if np.proper:
        return np.proper
    if np.pronoun:
        return np.pronoun
    if np.is_wh and np.head_is_tp:
        return np.head

    parts: list[str] = []
    if np.head_is_tp:
        parts.append(np.head)
    elif np.head:
        parts.append(gloss(np.head, "n"))
    elif np.possessive is None and not np.adjectives and np.number is None:
        # Nothing else to realize either, so fall back to an unknown-noun
        # placeholder rather than rendering an empty NP.
        parts.append(UNKNOWN.format("?"))

    if np.possessive:
        parts.append(np.possessive)
    for j, adj in enumerate(np.adjectives):
        # The wh-marker "seme" is pushed onto `adjectives` as a literal TP
        # token (not an English lemma), so it must bypass gloss().
        parts.append(adj if adj == "seme" else gloss(adj, "mod"))
        if np.intensifier and j == len(np.adjectives) - 1:
            parts.append(np.intensifier)
    if np.number:
        parts.append(np.number)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Clause structure and parsing.
# ---------------------------------------------------------------------------

# Catenatives are deliberately excluded: they can be ordinary main verbs
# ("I want pizza"), so an NP scan must not treat them as a hard boundary.
STOP_FOR_NP = frozenset(
    set(PREP_MAP) | CONJUNCTIONS | set(SUBORDINATORS) | NEGATORS
    | COPULA_WORDS | AUX_DO | AUX_PERFECT | set(TRUE_MODAL_WORDS) | WH_WORDS
)

ADJUNCT_WH = frozenset(["when", "where", "why", "how"])

_WH_ADJUNCT_PREP = {"where": "lon", "why": "tan", "how": "kepeken", "when": "lon tenpo"}


def _next_is_verblike(tokens: list[Tok], i: int) -> bool:
    """True if tokens[i] exists and has a verb/pre-verb sense (used to decide
    whether a catenative word is acting as a pre-verb vs. a plain main verb)."""
    if i >= len(tokens):
        return False
    lemma = lemmatize(tokens[i].text)
    return any(h.role in ("v", "vt", "pre-verb") for h in reverse_lookup(lemma))


def _single_modal_match(tokens: list[Tok], i: int) -> str | None:
    """Resolve a single-word modal/catenative trigger at position i, if any."""
    word = tokens[i].text
    if word in TRUE_MODAL_WORDS:
        return TRUE_MODAL_WORDS[word]
    if word in CATENATIVE_WORDS and _next_is_verblike(tokens, i + 1):
        return CATENATIVE_WORDS[word]
    return None


def _is_fronted_aux_word(tokens: list[Tok], i: int) -> bool:
    word = tokens[i].text
    if word in COPULA_WORDS or word in AUX_DO or word in AUX_PERFECT:
        return True
    if word in TRUE_MODAL_WORDS:
        return True
    if word in CATENATIVE_WORDS:
        return _next_is_verblike(tokens, i + 1)
    return False


@dataclass
class Clause:
    subject: NP | None = None
    preverbs: list[str] = field(default_factory=list)
    negated: bool = False
    neg_scope: str = "verb"   # "modal" | "verb"
    is_yesno: bool = False
    copula: bool = False
    verb: str | None = None
    adjective: str | None = None
    adj_intensifier: str | None = None
    pred_noun: NP | None = None
    obj: NP | None = None
    pps: list[tuple[str, str]] = field(default_factory=list)
    tense: str = "present"    # "past" | "present"
    is_imperative: bool = False
    is_question: bool = False
    wh_role: str | None = None   # "subject" | "object" | "adjunct" | "predicate"
    wh_word: str | None = None


def _fronted_aux_tp(word: str) -> str:
    if word in COPULA_WORDS or word in AUX_DO or word in AUX_PERFECT:
        return ""
    return MODAL_WORDS.get(word, "")


# AUX_PERFECT words (have/has/had) double as the ordinary main verb "jo"
# (possess) when not actually heading a perfect construction, so the
# main-verb branch of parse_predicate must not treat them as closed-class.
_STOP_FOR_MAIN_VERB = STOP_FOR_NP - AUX_PERFECT


def _parse_copula_complement(tokens: list[Tok], i: int, clause: Clause) -> int:
    """Parse what follows an already-consumed copula: optional negation/
    intensifier, then a noun-phrase or adjective complement.

    Shared by `parse_predicate`'s own copula branch and by `parse_clause`'s
    fronted-aux question handling, where the copula word itself was already
    consumed earlier to extract the subject, so `parse_predicate` would never
    see it.
    """
    n = len(tokens)
    if i < n and tokens[i].text in NEGATORS:
        clause.negated = True
        clause.neg_scope = "verb"
        i += 1
    intens = None
    if i < n and tokens[i].text in INTENSIFIERS and i + 1 < n:
        intens = INTENSIFIERS[tokens[i].text]
        i += 1
    if i < n and (tokens[i].text in ARTICLES or tokens[i].text in POSSESSIVE_TP):
        m = parse_np(tokens, i, STOP_FOR_NP)
        if m:
            clause.pred_noun, i = m
    elif i < n and has_sense(lemmatize(tokens[i].text), "mod"):
        clause.adjective = lemmatize(tokens[i].text)
        clause.adj_intensifier = intens
        i += 1
    elif i < n and tokens[i].text not in STOP_FOR_NP:
        m = parse_np(tokens, i, STOP_FOR_NP)
        if m:
            clause.pred_noun, i = m
    return i


def parse_predicate(tokens: list[Tok], i: int, clause: Clause) -> int:
    n = len(tokens)

    if i < n and tokens[i].text in AUX_DO:
        if tokens[i].text in AUX_DO_PAST:
            clause.tense = "past"
        i += 1
    if i < n and tokens[i].text in NEGATORS:
        clause.negated = True
        clause.neg_scope = "verb"
        i += 1

    perfect = False
    if i < n and tokens[i].text in AUX_PERFECT:
        look = i + 1
        if look < n and tokens[look].text in NEGATORS:
            look += 1
        if look < n and (tokens[look].text == "been" or _next_is_verblike(tokens, look)):
            clause.tense = "past"
            perfect = True
            i += 1
            if i < n and tokens[i].text in NEGATORS:
                clause.negated = True
                clause.neg_scope = "verb"
                i += 1

    while i < n:
        matched: tuple[str, int] | None = None
        for phrase, tp in MODAL_PHRASES:
            words = phrase.split()
            seg = tokens[i : i + len(words)]
            # Phrases are stored with the bare infinitive "be" (e.g. "be
            # going to"); normalize inflected copula forms (am/is/was/...)
            # to "be" so "I am going to..." / "she was able to..." match.
            seg_words = [("be" if t.text in COPULA_WORDS else t.text) for t in seg]
            if len(seg) == len(words) and seg_words == words:
                if any(t.text in COPULA_PAST for t in seg):
                    clause.tense = "past"
                matched = (tp, len(words))
                break
        if matched is None:
            single = _single_modal_match(tokens, i)
            if single is not None:
                matched = (single, 1)
        if matched is None:
            break
        tp, length = matched
        clause.preverbs.extend(tp.split())
        i += length
        if i < n and tokens[i].text in NEGATORS:
            clause.negated = True
            clause.neg_scope = "modal"
            i += 1

    if i < n and tokens[i].text in COPULA_WORDS:
        if tokens[i].text in COPULA_PAST:
            clause.tense = "past"
        clause.copula = True
        i += 1
        return _parse_copula_complement(tokens, i, clause)

    if i < n and tokens[i].text not in _STOP_FOR_MAIN_VERB:
        surface = tokens[i].text
        if perfect or verb_tense(surface) == "past":
            clause.tense = "past"
        clause.verb = lemmatize(surface)
        i += 1

    if i < n and not clause.copula:
        m = parse_np(tokens, i, STOP_FOR_NP)
        if m:
            clause.obj, i = m

    while i < n and tokens[i].text in PREP_MAP:
        prep_tp = PREP_MAP[tokens[i].text]
        i += 1
        m = parse_np(tokens, i, STOP_FOR_NP)
        if not m:
            break
        np_obj, i = m
        clause.pps.append((prep_tp, realize_np(np_obj)))

    return i


def _finish(clause: Clause) -> Clause:
    if clause.wh_role == "adjunct" and clause.wh_word:
        prep_tp = _WH_ADJUNCT_PREP.get(clause.wh_word)
        if prep_tp:
            clause.pps.append((prep_tp, "seme"))
    return clause


def parse_clause(tokens: list[Tok]) -> Clause:
    clause = Clause()
    n = len(tokens)
    i = 0

    wh_word: str | None = None
    wh_np: NP | None = None

    if i < n and (
        tokens[i].text in ("which", "whose")
        or (i + 1 < n and _WH_HOW_MANY_RE.match(f"{tokens[i].text} {tokens[i + 1].text}"))
    ):
        # Must be checked before the bare ADJUNCT_WH "how" match below, since
        # "how" is itself in ADJUNCT_WH but "how many/much X" is an NP, not
        # an adjunct.
        m = parse_np(tokens, i, STOP_FOR_NP)
        if m:
            wh_np, i = m
            wh_word = wh_np.wh_word
    elif i < n and tokens[i].text in ADJUNCT_WH:
        wh_word = tokens[i].text
        i += 1
    elif i < n and tokens[i].text in ("who", "what"):
        wh_word = tokens[i].text
        wh_np = NP(head="seme", head_is_tp=True, is_wh=True, wh_word=wh_word)
        i += 1

    if wh_word is not None and wh_word in ADJUNCT_WH and not (i < n and _is_fronted_aux_word(tokens, i)):
        clause.wh_role = "adjunct"
        clause.wh_word = wh_word
        clause.is_question = True
        sm = parse_np(tokens, i, STOP_FOR_NP)
        if sm:
            clause.subject, i = sm
        parse_predicate(tokens, i, clause)
        return _finish(clause)

    if i < n and _is_fronted_aux_word(tokens, i):
        aux_word = tokens[i].text
        aux_tp = _fronted_aux_tp(aux_word)
        fronted_copula = aux_word in COPULA_WORDS
        if aux_word in COPULA_PAST or aux_word in AUX_DO_PAST:
            clause.tense = "past"
        if aux_tp:
            clause.preverbs.extend(aux_tp.split())
        i += 1
        if i < n and tokens[i].text in NEGATORS:
            clause.negated = True
            clause.neg_scope = "modal" if aux_tp else "verb"
            i += 1
        sm = parse_np(tokens, i, STOP_FOR_NP)
        if sm:
            clause.subject, i = sm
        clause.is_question = True
        if wh_word is None:
            clause.is_yesno = not clause.negated

        if fronted_copula and wh_np is not None and (i >= n or tokens[i].text in CONJUNCTIONS):
            clause.copula = True
            clause.pred_noun = wh_np
            clause.wh_role = "predicate"
            clause.wh_word = wh_word
            return _finish(clause)

        if fronted_copula:
            # The copula word itself was already consumed above (to find the
            # subject), so `parse_predicate` would never see it -- parse the
            # complement directly instead.
            clause.copula = True
            i = _parse_copula_complement(tokens, i, clause)
        else:
            parse_predicate(tokens, i, clause)
        if wh_np is not None:
            clause.wh_word = wh_word
            if wh_word in ADJUNCT_WH:
                clause.wh_role = "adjunct"
            else:
                clause.wh_role = "object"
                if clause.copula:
                    if clause.pred_noun is None and clause.adjective is None:
                        clause.pred_noun = wh_np
                elif clause.obj is None:
                    clause.obj = wh_np
        elif wh_word is not None:
            clause.wh_role = "adjunct"
            clause.wh_word = wh_word
        return _finish(clause)

    if wh_word is not None:
        clause.subject = wh_np if wh_np is not None else NP(head="seme", head_is_tp=True)
        clause.wh_role = "subject"
        clause.wh_word = wh_word
        clause.is_question = True
        parse_predicate(tokens, i, clause)
        return _finish(clause)

    sm = parse_np(tokens, i, STOP_FOR_NP)
    if sm:
        clause.subject, i = sm
        parse_predicate(tokens, i, clause)
        return _finish(clause)

    clause.is_imperative = True
    parse_predicate(tokens, i, clause)
    return _finish(clause)


# ---------------------------------------------------------------------------
# Clause realization (Toki Pona output).
# ---------------------------------------------------------------------------

def _apply_negation(tokens_list: list[str], scope: str, negated: bool, is_yesno: bool) -> list[str]:
    if not tokens_list or (not negated and not is_yesno):
        return tokens_list
    preverb_count = len(tokens_list) - 1 if scope == "verb" else 0
    target_idx = len(tokens_list) - 1
    if scope == "modal":
        # The last preverb token sits before the main predicate token (if any).
        target_idx = max(0, len(tokens_list) - 2) if len(tokens_list) > 1 else 0
    word = tokens_list[target_idx]
    if is_yesno:
        tokens_list[target_idx] = f"{word} ala {word}"
    else:
        tokens_list[target_idx] = f"{word} ala"
    return tokens_list


def realize_clause(clause: Clause) -> str:
    subject_str = realize_np(clause.subject) if clause.subject else ""
    li = " li" if subject_str and subject_str not in ("mi", "sina") else ""

    main = ""
    if clause.copula:
        if clause.adjective:
            main = gloss(clause.adjective, "mod")
            if clause.adj_intensifier:
                main = f"{main} {clause.adj_intensifier}"
        elif clause.pred_noun:
            main = realize_np(clause.pred_noun)
    elif clause.verb:
        has_obj = clause.obj is not None
        roles = ("vt", "v") if has_obj else ("v", "vt")
        main = gloss(clause.verb, *roles, "pre-verb")

    predicate_tokens = list(clause.preverbs)
    if main:
        predicate_tokens.append(main)
    predicate_tokens = _apply_negation(predicate_tokens, clause.neg_scope, clause.negated, clause.is_yesno)
    predicate_str = " ".join(predicate_tokens)

    obj_str = f" e {realize_np(clause.obj)}" if clause.obj else ""
    pps_str = "".join(f" {prep} {obj}" for prep, obj in clause.pps)

    if clause.is_imperative:
        body = f"o {predicate_str}{obj_str}{pps_str}".strip()
    else:
        tense_prefix = "tenpo pini la " if clause.tense == "past" else ""
        body = f"{tense_prefix}{subject_str}{li} {predicate_str}{obj_str}{pps_str}"
        body = re.sub(r"\s+", " ", body).strip()

    if clause.is_question:
        body += "?"
    elif clause.is_imperative:
        body += "!"
    return body


# ---------------------------------------------------------------------------
# Coordinate / subordinate clause splitting and sentence assembly.
# ---------------------------------------------------------------------------

@dataclass
class TpResult:
    readings: list[str]
    note: str | None = None


def _split_top_conjunction(tokens: list[Tok]) -> tuple[list[Tok], str, list[Tok]] | None:
    """Split on a top-level and/but/or, ignoring ones inside a subordinate clause."""
    for idx, tok in enumerate(tokens):
        if tok.text in CONJUNCTIONS and 0 < idx < len(tokens) - 1:
            return tokens[:idx], tok.text, tokens[idx + 1 :]
    return None


def _split_subordinate(tokens: list[Tok]) -> tuple[str, list[Tok], list[Tok]] | None:
    """Detect a leading or comma-separated subordinate clause."""
    if tokens and tokens[0].text in SUBORDINATORS:
        sub_word = tokens[0].text
        rest = tokens[1:]
        # Split at the first comma-less boundary: look for a second clause
        # introduced once the subordinate clause's own subject+predicate is
        # complete. We approximate by splitting on a following subject
        # pronoun/proper-noun run preceded by enough tokens to form a clause.
        for idx in range(1, len(rest)):
            if rest[idx].text in PRONOUN_TP and idx >= 2:
                return sub_word, rest[:idx], rest[idx:]
        return None
    for idx, tok in enumerate(tokens):
        if idx > 0 and tok.text in SUBORDINATORS:
            sub_word = tok.text
            return sub_word, tokens[idx + 1 :], tokens[:idx]
    return None


def _realize_token_clause(tokens: list[Tok]) -> str:
    return realize_clause(parse_clause(tokens))


def _bare_predicate_str(clause: Clause) -> str:
    """Realize just the predicate/object/PPs of a clause, with no subject."""
    return realize_clause(replace(clause, subject=None))


def _parse_coordinate_conjunct(tokens: list[Tok], left_clause: Clause) -> Clause:
    """Parse the right-hand side of an 'and'/'or' split.

    English VP-coordination ("I eat fish and drink water") and predicate-
    nominal coordination ("She is a soldier and a leader") both drop the
    subject (and, for the latter, the copula) on the second conjunct
    entirely, which `parse_clause` would otherwise misread as an imperative
    or a fresh article-led subject. Try a bare-predicate/-complement parse
    first (sharing the left clause's subject) and only fall back to a full
    clause parse when the fragment actually starts a new subject of its own.
    """
    if left_clause.copula:
        bare = Clause()
        end = _parse_copula_complement(tokens, 0, bare)
        if end == len(tokens) and (bare.pred_noun or bare.adjective):
            bare.copula = True
            return _finish(bare)

    if tokens and (
        tokens[0].is_proper
        or tokens[0].text in PRONOUN_TP
        or tokens[0].text in ARTICLES
        or tokens[0].text in POSSESSIVE_TP
    ):
        return parse_clause(tokens)
    bare = Clause()
    end = parse_predicate(tokens, 0, bare)
    if end == len(tokens) and (bare.verb or bare.copula or bare.preverbs):
        return _finish(bare)
    return parse_clause(tokens)


def translate_one_clause_tokens(tokens: list[Tok]) -> str:
    if not tokens:
        return ""

    sub = _split_subordinate(tokens)
    if sub:
        sub_word, sub_tokens, main_tokens = sub
        marker = SUBORDINATORS[sub_word]
        sub_str = _realize_token_clause(sub_tokens).rstrip("?!")
        main_str = translate_one_clause_tokens(main_tokens) if main_tokens else ""
        if marker == "taso":
            return f"{sub_str}. taso {main_str}".strip()
        return f"{sub_str} {marker} {main_str}".strip()

    coord = _split_top_conjunction(tokens)
    if coord:
        left, conj, right = coord
        left_clause = parse_clause(left)
        right_clause = _parse_coordinate_conjunct(right, left_clause) if conj != "but" else parse_clause(right)
        left_str = realize_clause(left_clause)

        shares_subject = False
        if conj in ("and", "or") and left_clause.subject is not None and not left_clause.is_imperative:
            if right_clause.subject is None and not right_clause.is_imperative:
                shares_subject = True
            elif right_clause.subject is not None and (
                realize_np(left_clause.subject) == realize_np(right_clause.subject)
            ):
                shares_subject = True

        if shares_subject:
            right_pred_str = _bare_predicate_str(right_clause)
            left_body = left_str.rstrip("?!.")
            trailing = left_str[len(left_body):]
            joiner = "li" if conj == "and" else "anu"
            return f"{left_body} {joiner} {right_pred_str}{trailing}"

        right_str = realize_clause(right_clause)
        if conj == "and":
            return f"{left_str.rstrip('?!.')}. {right_str}"
        if conj == "but":
            return f"{left_str.rstrip('?!.')}. taso {right_str}"
        return f"{left_str.rstrip('?!.')} anu {right_str}"

    return _realize_token_clause(tokens)


def _unknown_words(tokens: list[Tok]) -> list[str]:
    out: list[str] = []
    for tok in tokens:
        if tok.is_proper or tok.text in STOP_FOR_NP or tok.text in PRONOUN_TP:
            continue
        if tok.text in ARTICLES or tok.text in POSSESSIVE_TP or tok.text in INTENSIFIERS:
            continue
        if tok.text in ABSOLUTE_POSSESSIVE_TP:
            continue
        if not reverse_lookup(lemmatize(tok.text)):
            out.append(tok.raw)
    return out


def translate_one_sentence_tp(text: str, max_candidates: int = 3) -> TpResult:
    tokens = tokenize_en(expand_contractions(text))
    if not tokens:
        return TpResult([], "Nothing to translate.")

    tp_word_count = sum(1 for t in tokens if t.text in LEXICON or t.text in COMPOUNDS)
    if len(tokens) >= 2 and tp_word_count / len(tokens) >= 0.6:
        return TpResult(
            [],
            "This looks like Toki Pona already. Swap directions to translate it into English.",
        )

    primary = translate_one_clause_tokens(tokens)
    readings = [primary] if primary else []

    unknowns = _unknown_words(tokens)
    note = f"No Toki Pona word for: {', '.join(unknowns)}." if unknowns else None
    return TpResult(readings[:max_candidates], note)


def translate_to_toki_pona(text: str, max_candidates: int = 3) -> TpResult:
    sentences = segment_sentences_en(text)
    if not sentences:
        return TpResult([], "Nothing to translate.")
    if len(sentences) == 1:
        return translate_one_sentence_tp(sentences[0], max_candidates)

    parts = [translate_one_sentence_tp(s, max_candidates) for s in sentences]
    notes = [p.note for p in parts if p.note]
    primary = ". ".join(p.readings[0] if p.readings else "(…)" for p in parts)
    note = " ".join(notes) if notes else f"{len(sentences)} sentences."
    return TpResult([primary], note)
