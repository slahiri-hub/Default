"""Toki Pona -> English translation: particle-grammar parser + realizer.

Ported from the original translatorengine.js. Toki Pona's particle grammar
([CONTEXT la] SUBJECT (li PREDICATE)* with e-objects and prepositional
phrases) is parsed into a structure, then each predicate/NP is realized into
English by enumerating lexical-sense and structural-role choices. Ambiguity
is real (a predicate word can read as verb or adjective; a content word has
several glosses), so we enumerate bounded combinations and return the top N
distinct readings rather than picking one "correct" answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .lexicon import COMPOUNDS, LEXICON, PREVERBS
from .tokenizer import Correction, is_proper_name, tokenize

PREPOSITIONS = frozenset(["tawa", "tan", "lon", "kepeken", "sama", "poka", "insa"])

NUMBER_OR_DESC = frozenset(["wan", "tu", "mute", "ale", "ali", "taso"])
NUMBER_WORDS = frozenset(["wan", "tu", "mute", "ale", "ali"])


# ---- parse tree ----


@dataclass
class Mod:
    word: str | None = None
    group: "Phrase | None" = None
    negated: bool = False


@dataclass
class Phrase:
    head: str
    mods: list[Mod]
    next: int


@dataclass
class PrepPhrase:
    prep: str
    phrase: Phrase


@dataclass
class Predicate:
    phrase: Phrase
    objects: list[Phrase]
    preverbs: list[str]
    negated: bool
    prep_phrases: list[PrepPhrase]


@dataclass
class ParsedSentence:
    context: list[str] | None
    conjunction: str | None
    imperative: bool
    optative: bool
    is_question: bool
    has_seme: bool
    subjects: list[Phrase]
    predicates: list[Predicate]
    subj_is_short: bool
    corrections: list[Correction]
    tokens: list[str]
    error: str | None = None


def has_role(word: str, role: str) -> bool:
    entry = LEXICON.get(word)
    return bool(entry and entry.get(role))


def parse_phrase(tokens: list[str], i: int, stop_set: frozenset[str]) -> Phrase | None:
    """A modified phrase: head word + modifiers; 'pi' regroups into a sub-phrase."""
    head = tokens[i] if i < len(tokens) else None
    if head is None:
        return None
    j = i + 1
    mods: list[Mod] = []
    while j < len(tokens) and tokens[j] not in stop_set:
        if tokens[j] == "pi":
            sub = parse_phrase(tokens, j + 1, stop_set)
            if not sub:
                break
            mods.append(Mod(group=sub))
            j = sub.next
        else:
            mods.append(Mod(word=tokens[j]))
            j += 1
    return Phrase(head=head, mods=mods, next=j)


def parse_object_phrase(tokens: list[str], i: int, stop_set: frozenset[str]) -> Phrase | None:
    """Like parse_phrase, but a preposition completing a known compound (e.g.
    "sitelen tawa" = movie) is absorbed as a modifier instead of ending the
    phrase, resolving the ambiguity in favor of the lexicalized reading."""
    head = tokens[i] if i < len(tokens) else None
    if head is None:
        return None
    j = i + 1
    mods: list[Mod] = []
    while j < len(tokens) and tokens[j] not in stop_set:
        if tokens[j] in PREPOSITIONS:
            key = f"{head} {tokens[j]}"
            if key in COMPOUNDS:
                mods.append(Mod(word=tokens[j]))
                j += 1
                continue
            break
        if tokens[j] == "pi":
            sub = parse_phrase(tokens, j + 1, stop_set)
            if not sub:
                break
            mods.append(Mod(group=sub))
            j = sub.next
        else:
            mods.append(Mod(word=tokens[j]))
            j += 1
    return Phrase(head=head, mods=mods, next=j)


def parse_phrase_stopping_at_prep(tokens: list[str], i: int, stop_set: frozenset[str]) -> Phrase | None:
    """Like parse_phrase, but stops when a preposition appears in non-head
    position (the head itself may be a preposition word acting as a verb)."""
    head = tokens[i] if i < len(tokens) else None
    if head is None:
        return None
    j = i + 1
    mods: list[Mod] = []
    while j < len(tokens) and tokens[j] not in stop_set:
        if tokens[j] in PREPOSITIONS:
            break
        if tokens[j] == "pi":
            sub = parse_phrase(tokens, j + 1, stop_set)
            if not sub:
                break
            mods.append(Mod(group=sub))
            j = sub.next
        else:
            mods.append(Mod(word=tokens[j]))
            j += 1
    return Phrase(head=head, mods=mods, next=j)


def parse_toki_pona(text: str) -> ParsedSentence:
    corrections: list[Correction] = []
    tokens = tokenize(text, corrections)
    if not tokens:
        return ParsedSentence(
            context=None, conjunction=None, imperative=False, optative=False,
            is_question=False, has_seme=False, subjects=[], predicates=[],
            subj_is_short=False, corrections=corrections, tokens=tokens,
            error="Nothing to translate.",
        )

    conjunction = None
    if len(tokens) > 1 and tokens[0] == "taso":
        conjunction = "but"
        tokens = tokens[1:]

    context = None
    body = tokens
    if "la" in tokens:
        la_idx = tokens.index("la")
        if la_idx > 0:
            context = tokens[:la_idx]
            body = tokens[la_idx + 1 :]

    if len(body) > 1 and body[-1] == "a":
        body = body[:-1]

    tag_question = False
    if len(body) >= 2 and body[-2] == "anu" and body[-1] == "seme":
        tag_question = True
        body = body[:-2]

    imperative = False
    if body and body[0] == "o":
        imperative = True
        body = body[1:]

    # --- subject phrase(s), joined by "en" ---
    subjects: list[Phrase] = []
    k = 0
    subj_stop = frozenset(["li", "o", "e", "en"])

    has_li = "li" in body
    after1 = body[1] if len(body) > 1 else None
    after_starts_predicate = (
        after1 is not None
        and after1 not in NUMBER_OR_DESC
        and (
            after1 in PREVERBS
            or has_role(after1, "v")
            or has_role(after1, "vt")
            or has_role(after1, "mod")
            or has_role(after1, "n")
        )
    )
    short_subj = (
        bool(body)
        and body[0] in ("mi", "sina")
        and after1 is not None
        and after1 != "li"
        and after1 != "o"
        and (not has_li or after_starts_predicate)
    )

    if short_subj:
        subjects.append(Phrase(head=body[0], mods=[], next=1))
        k = 1
    else:
        while k < len(body):
            ph = parse_phrase(body, k, subj_stop)
            if not ph:
                break
            subjects.append(ph)
            k = ph.next
            if k < len(body) and body[k] == "en":
                k += 1
                continue
            break

    optative = False
    if k < len(body) and body[k] == "o":
        optative = True
        imperative = True
        k += 1

    subj_is_short = short_subj

    predicates: list[Predicate] = []

    if (
        imperative
        and not optative
        and (not subjects or k >= len(body) or body[k] != "li")
        and not short_subj
    ):
        k = 0
        subjects = []

    first_pred = True
    is_question = False
    while k < len(body):
        if body[k] == "li":
            k += 1
        elif first_pred and (short_subj or imperative):
            pass
        elif first_pred:
            break
        else:
            break
        first_pred = False

        # Peel off a chain of pre-verbs, e.g. "wile ala moku" = "do not want to
        # eat"; "ken ala ken" (reduplication) signals a yes/no question.
        preverbs: list[str] = []
        preverb_negated = False
        while k < len(body) and body[k] in PREVERBS:
            after = body[k + 1] if k + 1 < len(body) else None
            if after == "ala" and k + 2 < len(body) and body[k + 2] == body[k]:
                preverbs.append(body[k])
                is_question = True
                k += 3
                continue
            if after == "ala" and k + 2 < len(body) and body[k + 2] not in ("li", "e"):
                preverbs.append(body[k])
                preverb_negated = True
                k += 2
                continue
            # A pre-verb followed by a preposition has no verb complement; the
            # pre-verb is the predicate verb itself ("awen lon ni" = "stay at this").
            if after is not None and after in PREPOSITIONS:
                break
            if after is not None and after not in ("li", "e", "ala"):
                preverbs.append(body[k])
                k += 1
                continue
            break

        # Pre-verbs consumed but nothing can follow as a complement: the last
        # pre-verb is actually the main verb ("lukin ala lukin" = "do you look?").
        if preverbs and (k >= len(body) or body[k] == "li"):
            last_pv = preverbs.pop()
            pred_phrase = Phrase(head=last_pv, mods=[], next=k)
            predicates.append(
                Predicate(phrase=pred_phrase, objects=[], preverbs=preverbs,
                          negated=preverb_negated, prep_phrases=[])
            )
            if k >= len(body) or body[k] != "li":
                break
            continue

        pred_stop = frozenset(["li", "e", "ala"])
        pred_phrase = parse_phrase_stopping_at_prep(body, k, pred_stop)
        if not pred_phrase:
            break
        k = pred_phrase.next

        negated = preverb_negated
        if k < len(body) and body[k] == "ala" and k + 1 < len(body) and body[k + 1] == pred_phrase.head:
            is_question = True
            k += 2
        elif k < len(body) and body[k] == "ala":
            if pred_phrase.mods:
                pred_phrase.mods[-1].negated = True
            else:
                negated = True
            k += 1

        objects: list[Phrase] = []
        while k < len(body) and body[k] == "e":
            obj_stop = frozenset(["li", "e"])
            obj = parse_object_phrase(body, k + 1, obj_stop)
            if not obj:
                break
            objects.append(obj)
            k = obj.next

        prep_phrases: list[PrepPhrase] = []
        while k < len(body) and body[k] in PREPOSITIONS:
            prep = body[k]
            pp_stop = frozenset(["li", "e", "ala"])
            pp_obj = parse_phrase_stopping_at_prep(body, k + 1, pp_stop)
            if not pp_obj:
                break
            prep_phrases.append(PrepPhrase(prep=prep, phrase=pp_obj))
            k = pp_obj.next

        predicates.append(
            Predicate(phrase=pred_phrase, objects=objects, preverbs=preverbs,
                      negated=negated, prep_phrases=prep_phrases)
        )
        if k >= len(body) or body[k] != "li":
            break

    has_seme = "seme" in tokens

    return ParsedSentence(
        context=context,
        conjunction=conjunction,
        imperative=imperative,
        optative=optative,
        is_question=is_question or tag_question or has_seme,
        has_seme=has_seme,
        subjects=subjects,
        predicates=predicates,
        subj_is_short=subj_is_short,
        corrections=corrections,
        tokens=tokens,
    )


# ---- realization ----

_FALLBACK_ROLES = ("n", "v", "mod", "prep", "number", "interj", "pre-verb")


def senses(word: str, role: str | None) -> list[str]:
    if is_proper_name(word):
        return [word]
    entry = LEXICON.get(word)
    if not entry:
        return [f"⟨{word}?⟩"]
    if role and entry.get(role):
        return entry[role]
    for r in _FALLBACK_ROLES:
        if entry.get(r):
            return entry[r]
    return [f"⟨{word}⟩"]


OBJECTIVE_CASE = {"I": "me", "we": "us", "he": "him", "she": "her", "they": "them"}


def to_objective_case(word: str) -> str:
    return OBJECTIVE_CASE.get(word, word)


def realize_np(phrase: Phrase, cap: int = 3, objective: bool = False) -> list[str]:
    # Bare "seme" or "<noun> seme" fronts a wh-word marker that to_question() picks up.
    if phrase.head == "seme" and not phrase.mods:
        return ["⟦what⟧"]
    if any(m.word == "seme" for m in phrase.mods):
        h = phrase.head
        if h == "jan":
            return ["⟦who⟧"]
        if h == "ijo":
            return ["⟦what⟧"]
        if h == "tenpo":
            return ["⟦when⟧"]
        if h in ("ma", "lon"):
            return ["⟦where⟧"]
        noun = senses(h, "n")[0]
        return [f"⟦which {noun}⟧"]

    compound_readings = match_compound(phrase, objective)

    head_senses = senses(phrase.head, "n")[:cap]
    if objective:
        head_senses = [to_objective_case(h) for h in head_senses]

    possessives: list[str] = []
    descriptors: list[str] = []
    names: list[str] = []
    for m in phrase.mods:
        if m.group:
            descriptors.append(realize_np(m.group, 1)[0])
        elif is_proper_name(m.word):
            names.append(m.word)
        elif m.word in ("mi", "sina", "ona"):
            possessives.append(senses(m.word, "mod")[0])
        else:
            descriptors.append(senses(m.word, "mod")[0])

    results: list[str] = []
    for h in head_senses:
        # "jan <Name>" (person classifier + name) drops to just the name, as
        # classifiers aren't used with personal names in English.
        if names and phrase.head == "jan" and not possessives and not descriptors:
            results.append(" ".join(names))
        else:
            parts = [p for p in (*possessives, *descriptors, *names, h) if p]
            results.append(" ".join(parts))
    return [*compound_readings, *results]


def match_predicate_compound(phrase: Phrase) -> list[str]:
    if not phrase.mods or phrase.mods[0].group:
        return []
    key = f"{phrase.head} {phrase.mods[0].word}"
    entry = COMPOUNDS.get(key)
    if entry and entry.get("v"):
        return entry["v"][:3]
    return []


def match_compound(phrase: Phrase, objective: bool) -> list[str]:
    if not phrase.mods:
        return []
    mod_words: list[str] = []
    for m in phrase.mods:
        if m.group:
            break
        mod_words.append(m.word)

    for take in range(min(len(mod_words), 2), 0, -1):
        key = " ".join([phrase.head, *mod_words[:take]])
        entry = COMPOUNDS.get(key)
        if not entry:
            continue
        sense_list = (entry.get("n") or entry.get("mod") or [])[:3]
        if not sense_list:
            continue
        leftover = phrase.mods[take:]
        extra_desc = [
            d
            for d in (
                realize_np(m.group, 1)[0] if m.group else senses(m.word, "mod")[0]
                for m in leftover
            )
            if d
        ]
        possess: list[str] = []
        descr: list[str] = []
        for d in extra_desc:
            if d in ("my", "your", "its", "his", "her", "our", "their"):
                possess.append(d)
            else:
                descr.append(d)
        results = []
        for s in sense_list:
            val = to_objective_case(s) if objective else s
            parts = [p for p in (*possess, *descr, val) if p]
            results.append(" ".join(parts))
        return results
    return []


# Verb senses that take an English preposition before their object ("look at").
VERB_PREP = {"look": "at", "listen": "to", "wait": "for", "search": "for", "hunt": "for"}

# "<prep> seme" frames map to a fronted wh-word ("tan seme" = "from what" = why).
PREP_SEME_WH = {
    "tan": "why",
    "lon": "where",
    "tawa": "where to",
    "kepeken": "how",
    "sama": "like what",
    "poka": "beside what",
    "insa": "inside what",
}

MOD_ANTONYM = {
    "strong": "weak", "strongly": "weakly", "big": "small", "small": "big",
    "good": "bad", "bad": "good", "same": "different", "similar": "different",
    "hot": "cold", "cold": "hot", "new": "old", "many": "few", "fast": "slow",
    "high": "low", "full": "empty", "hard": "soft", "light": "dark",
}


def mod_with_neg(word: str, negated: bool) -> str:
    if not negated:
        return word
    return MOD_ANTONYM.get(word, f"not {word}")


# Intensifying-adverb readings for words modifying an adjective ("seli mute" = "very hot").
INTENSIFIER = {"mute": "very", "wawa": "strongly", "a": "really", "kin": "indeed"}


def pred_modifier(word: str, adjectival: bool) -> str:
    if adjectival and word in INTENSIFIER:
        return INTENSIFIER[word]
    return senses(word, "mod")[0]


# Adverbial readings for words modifying a verb.
VERB_ADVERB = {"mute": "a lot", "wawa": "strongly", "lili": "a little", "a": "really", "kin": "indeed"}


def verb_adverb(word: str) -> str:
    return VERB_ADVERB.get(word, senses(word, "mod")[0])


def article(noun: str) -> str:
    return "an " if re.match(r"^[aeiou]", noun, re.I) else "a "


def plural(copula: str) -> bool:
    return copula == "are"


# Abstract/mass nouns that shouldn't take an indefinite article ("become wisdom").
MASS_NOUNS = frozenset([
    "knowledge", "wisdom", "size", "importance", "goodness", "badness", "evil",
    "love", "compassion", "strength", "power", "energy", "water", "liquid",
    "fluid", "air", "breath", "spirit", "essence", "light", "brightness",
    "heat", "warmth", "cold", "coolness", "darkness", "money", "wealth",
    "time", "speech", "language", "truth", "presence", "novelty", "absence",
    "movement", "motion", "sex", "fun", "art", "sound", "noise", "smallness",
    "strangeness", "unity", "everything", "nothing", "difference", "change",
])


def is_mass_noun(noun: str) -> bool:
    return noun.split(" ")[-1] in MASS_NOUNS


def gerund(verb: str) -> str:
    w = verb.split(" ")[0]
    if w.endswith("e") and len(w) > 2 and not w.endswith("ee"):
        g = w[:-1] + "ing"
    else:
        g = w + "ing"
    return g + verb[len(w) :]


def wrap_preverbs(preverbs: list[str], complement: str) -> list[str]:
    """Wrap a complement ("to eat") in a pre-verb chain, right-to-left so the
    innermost pre-verb binds tightest, surfacing idiomatic phrasings."""
    phrasings = [complement]
    for pv in reversed(preverbs):
        nxt: list[str] = []
        for inner in phrasings:
            bare = re.sub(r"^to ", "", inner)
            if pv == "wile":
                nxt.append(f"want {inner}")
                nxt.append(f"need {inner}")
            elif pv == "ken":
                nxt.append(f"can {bare}")
            elif pv == "kama":
                if bare == "know":
                    nxt.append("come to know")
                    nxt.append("learn")
                elif bare.startswith("be "):
                    nxt.append(f"become {bare[3:]}")
                else:
                    nxt.append(f"come {inner}")
                    nxt.append(f"start {gerund(bare)}")
            elif pv == "awen":
                nxt.append(f"keep {gerund(bare)}")
                nxt.append(f"continue {inner}")
            elif pv in ("lukin", "alasa"):
                nxt.append(f"try {inner}")
                nxt.append(f"seek {inner}")
            elif pv == "sona":
                nxt.append(f"know how {inner}")
            else:
                nxt.append(f"{pv} {inner}")
        phrasings = nxt
    return phrasings


def realize_objects(objects: list[Phrase], cap: int, verb_prep: str | None = None) -> list[str]:
    if not objects:
        return [""]
    first_variants = realize_np(objects[0], cap, True)
    rest = [realize_np(o, cap, True)[0] for o in objects[1:]]
    out = []
    for first in first_variants:
        joined = " and ".join([first, *rest])
        out.append(f" {verb_prep} {joined}" if verb_prep else f" {joined}")
    return out


_IRREGULAR_3SG = {"have": "has", "be": "is", "do": "does", "go": "goes"}


def conjugate3sg(verb: str) -> str:
    w = verb.split(" ")[0]
    rest = verb[len(w) :]
    if w in _IRREGULAR_3SG:
        return _IRREGULAR_3SG[w] + rest
    if re.search(r"(s|sh|ch|x|z|o)$", w):
        g = w + "es"
    elif re.search(r"[^aeiou]y$", w):
        g = w[:-1] + "ies"
    else:
        g = w + "s"
    return g + rest


def negate_preverb(reading: str, copula: str) -> str:
    if re.match(r"^can\b", reading):
        return re.sub(r"^can\b", "cannot", reading)
    if re.match(r"^(is|are|am)\b", reading):
        return re.sub(r"^(is|are|am)\b", r"\1 not", reading)
    aux = "does not" if copula == "is" else "do not"
    return f"{aux} {reading}"


def negate(reading: str, copula: str) -> str:
    if re.match(r"^(is|are|am)\b", reading):
        return re.sub(r"^(is|are|am)\b", r"\1 not", reading)
    if re.match(r"^can\b", reading):
        return re.sub(r"^can\b", "cannot", reading)
    aux = "does not" if copula == "is" else "do not"
    return f"{aux} {reading}"


def to_imperative(reading: str) -> str:
    r = re.sub(r"^to ", "", reading)
    r = re.sub(r"^can ", "be able to ", r)
    return r


def append_pps(readings: list[str], pred: Predicate, copula: str) -> list[str]:
    pps = pred.prep_phrases or []
    if not pps:
        return readings
    pp_parts = []
    for pp in pps:
        if pp.phrase.head == "seme" and not pp.phrase.mods:
            pp_parts.append(f"⟦{PREP_SEME_WH.get(pp.prep, 'what')}⟧")
            continue
        if any(m.word == "seme" for m in pp.phrase.mods):
            pp_parts.append(f"⟦{PREP_SEME_WH.get(pp.prep, 'what')}⟧")
            continue
        prep_word = senses(pp.prep, "prep")[0]
        np = realize_np(pp.phrase, 1, True)[0]
        pp_parts.append(f"{prep_word} {np}")
    pp_str = " ".join(pp_parts)
    return [f"{r} {pp_str}".strip() for r in readings]


def realize_predicate(
    pred: Predicate,
    subject_plural: bool,
    cap: int = 3,
    copula: str = "is",
    imperative: bool = False,
) -> list[str]:
    head = pred.phrase.head
    opts: list[str] = []
    preverbs = pred.preverbs or []

    if head in PREPOSITIONS and any(m.word == "seme" for m in pred.phrase.mods):
        return [f"⟦{PREP_SEME_WH.get(head, 'what')}⟧"]
    if head == "seme" and not pred.phrase.mods and not pred.objects:
        return [f"{copula} ⟦what⟧"]

    if preverbs:
        has_object = bool(pred.objects)
        complement_forms: list[str] = []
        pv_compound = COMPOUNDS.get(f"{' '.join(preverbs)} {head}")
        pv_idiom_forms = pv_compound["v"][:cap] if pv_compound and pv_compound.get("v") else []
        for cv in match_predicate_compound(pred.phrase):
            complement_forms.append(f"to {cv}")
        # "kama" (inchoative) with an adjective-capable head usually means
        # "become <adjective>", so list that complement first.
        kama_inchoative = len(preverbs) == 1 and preverbs[0] == "kama"

        def push_verbs() -> None:
            if has_role(head, "v"):
                for v in senses(head, "v")[:cap]:
                    complement_forms.append(f"to {v}")

        def push_adj_noun() -> None:
            if not has_object and has_role(head, "mod"):
                for m in senses(head, "mod")[:cap]:
                    complement_forms.append(f"to be {m}")
            if not has_object and has_role(head, "n"):
                for n in senses(head, "n")[:cap]:
                    complement_forms.append(f"to be {n}" if is_mass_noun(n) else f"to be {article(n)}{n}")

        if kama_inchoative and has_role(head, "mod"):
            push_adj_noun()
            push_verbs()
        else:
            push_verbs()
            push_adj_noun()
        if not complement_forms:
            complement_forms.append(f"to {senses(head, None)[0]}")

        obj_strs = realize_objects(pred.objects, cap)

        third_sing = copula == "is" and not imperative
        for form in pv_idiom_forms:
            s = conjugate3sg(form) if third_sing else form
            for obj_str in obj_strs:
                opts.append(f"{s}{obj_str}".strip())

        for comp in complement_forms:
            for obj_str in obj_strs:
                for p in wrap_preverbs(preverbs, comp + obj_str):
                    opts.append(p.strip())

        deduped = list(dict.fromkeys(opts))[: cap * 4]
        if imperative:
            deduped = [to_imperative(r) for r in deduped]
        if pred.negated:
            negated = list(dict.fromkeys(
                (f"do not {r}" if imperative else negate_preverb(r, copula)) for r in deduped
            ))
        else:
            negated = deduped
        return append_pps(negated, pred, copula)

    # --- no pre-verb: plain verb / adjective-noun predicate ---
    pred_compound_verbs = match_predicate_compound(pred.phrase)
    if pred_compound_verbs:
        third_sing = copula == "is" and not imperative
        for v in pred_compound_verbs:
            s = conjugate3sg(v) if third_sing else v
            vp = VERB_PREP.get(v)
            for obj_str in realize_objects(pred.objects, cap, vp):
                opts.append(f"{s}{obj_str}".strip())
            if not pred.objects:
                opts.append(s.strip())

    has_object = bool(pred.objects)

    # Compound-noun predicate ("mi jan sona" = "I am an expert") ranks ahead of
    # a literal verb reading of the head (e.g. "jan" -> "personify").
    if not has_object:
        compound_noun_early = match_compound(pred.phrase, False)
        if compound_noun_early:
            cop = "be" if imperative else copula
            for c in compound_noun_early[:cap]:
                art = article(c) if (not plural(copula) and not is_mass_noun(c)) else ""
                opts.append(f"{cop} {art}{c}".strip())

    # Transitivity-sensitive verb reading: "vt" (causative) with an object if
    # available, else "v" (pona = "be good" intransitive / "improve" transitive).
    verb_role = ("vt" if has_role(head, "vt") else "v") if has_object else "v"
    if has_role(head, verb_role):
        third_sing = copula == "is" and not imperative
        for v in senses(head, verb_role)[:cap]:
            s = conjugate3sg(v) if third_sing else v
            adv = " ".join(
                realize_np(m.group, 1)[0] if m.group else mod_with_neg(verb_adverb(m.word), m.negated)
                for m in pred.phrase.mods
            )
            if adv:
                s += f" {adv}"
            vp = VERB_PREP.get(v)
            for obj_str in realize_objects(pred.objects, cap, vp):
                opts.append(f"{s}{obj_str}".strip())
            if not has_object:
                opts.append(s.strip())

    # Adjective/noun reading ("is X") — only valid with no object.
    if not has_object and (has_role(head, "mod") or has_role(head, "n")):
        cop = "be" if imperative else copula
        role = "mod" if has_role(head, "mod") else "n"
        adjectival = role == "mod"
        for d in senses(head, role)[:cap]:
            mods_str = " ".join(
                realize_np(m.group, 1)[0] if m.group else mod_with_neg(pred_modifier(m.word, adjectival), m.negated)
                for m in pred.phrase.mods
            )
            art = (
                article(d)
                if (not adjectival and not plural(copula) and not is_mass_noun(d) and not mods_str)
                else ""
            )
            opts.append(f"{cop} {mods_str + ' ' if mods_str else ''}{art}{d}".strip())

    base = opts if opts else [senses(head, None)[0]]
    if pred.negated:
        negated_base = list(dict.fromkeys(
            (f"do not {r}" if imperative else negate(r, copula)) for r in base
        ))
    else:
        negated_base = base
    return append_pps(negated_base, pred, copula)


# ---- subject / sentence assembly ----


@dataclass
class SubjectVariant:
    text: str
    copula: str
    plural: bool


@dataclass
class SubjectInfo:
    variants: list[SubjectVariant]
    plural: bool
    copula: str


def pronoun_subject_variants(subj: Phrase) -> list[SubjectVariant]:
    """Toki Pona pronouns are number-neutral ("mi" = I or we; "ona" = he/she/it
    or they); explicit number words (wan/tu/mute/ale) pin down which English
    pronoun(s) and agreement apply."""
    head = subj.head
    mod_words = [m.word for m in subj.mods]

    def has(w: str) -> bool:
        return w in mod_words

    number = None
    if has("wan"):
        number = "sg"
    elif has("tu") or has("mute") or has("ale") or has("ali"):
        number = "pl"

    desc_mods = [m for m in subj.mods if m.word not in NUMBER_WORDS]
    desc_str = " ".join(
        d
        for d in (
            realize_np(m.group, 1)[0] if m.group else senses(m.word, "mod")[0]
            for m in desc_mods
        )
        if d
    )

    def with_desc(pron: str) -> str:
        return f"{desc_str} {pron}" if desc_str else pron

    out: list[SubjectVariant] = []

    def push(text: str, copula: str, plural_: bool) -> None:
        out.append(SubjectVariant(with_desc(text), copula, plural_))

    if head == "mi":
        if number == "sg":
            push("I", "am", False)
        elif has("tu"):
            push("the two of us", "are", True)
        elif number == "pl":
            push("we", "are", True)
        else:
            push("I", "am", False)
            push("we", "are", True)
    elif head == "sina":
        push("you", "are", False)
    elif head == "ona":
        if number == "sg":
            push("it", "is", False)
        elif has("tu"):
            push("the two of them", "are", True)
        elif number == "pl":
            push("they", "are", True)
        else:
            push("it", "is", False)
            push("they", "are", True)
    elif head == "ni":
        if number == "pl":
            push("these", "are", True)
        else:
            push("this", "is", False)

    if not out:
        push(realize_np(subj, 1)[0], "is", False)
    return out


def subject_string(subjects: list[Phrase], subj_is_short: bool) -> SubjectInfo:
    if not subjects:
        return SubjectInfo(variants=[SubjectVariant("", "is", False)], plural=False, copula="is")
    if len(subjects) > 1:
        joined = " and ".join(realize_np(s, 1)[0] for s in subjects)
        return SubjectInfo(variants=[SubjectVariant(joined, "are", True)], plural=True, copula="are")

    subj = subjects[0]
    if subj.head in ("mi", "sina", "ona", "ni"):
        variants = pronoun_subject_variants(subj)
    else:
        variants = [SubjectVariant(text, "is", False) for text in realize_np(subj, 3)]
    return SubjectInfo(variants=variants, plural=variants[0].plural, copula=variants[0].copula)


def bounded_product(arrays: list[list[str]], max_n: int) -> list[list[str]]:
    out: list[list[str]] = [[]]
    for arr in arrays:
        nxt: list[list[str]] = []
        for prefix in out:
            for item in arr:
                nxt.append([*prefix, item])
                if len(nxt) >= max_n * 4:
                    break
        out = nxt
    return out[: max_n * 4]


_SENT_SPLIT_RE = re.compile(r"[.!?:]+")


def segment_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]


def subj_lower(s: str) -> str:
    return "I" if s.lower() == "i" else s.lower()


def cap1(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def lower_first(s: str) -> str:
    if re.match(r"^I\b", s):
        return s
    return s[:1].lower() + s[1:] if s else s


def undo3sg(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        stem, suf = m.group(1), m.group(2)
        if suf == "ies":
            return stem + "y"
        if suf == "es":
            if re.search(r"(ch|sh|x|z|s|o)$", stem):
                return stem
            return stem + "e"
        return stem

    return re.sub(r"^(\S+?)(ies|es|s)\b", repl, text)


def strip_command(s: str) -> str:
    return re.sub(r"!$", "", s)


_WH_RE = re.compile("⟦([^⟧]+)⟧")


def to_question(sentence: str) -> str:
    """Turn a declarative reading into a question. A fronted ⟦wh⟧ marker
    (left by a "seme" interrogative) is promoted to a wh-question; otherwise
    this is a yes/no question via subject-aux inversion."""
    s = re.sub(r"[.!]$", "", sentence)

    wh_match = _WH_RE.search(s)
    if wh_match:
        wh = wh_match.group(1)
        rest = re.sub("\\s*⟦[^⟧]+⟧\\s*", " ", s, count=1)
        rest = re.sub(r"\s+", " ", rest).strip()
        rest = _WH_RE.sub(r"\1", rest)

        starts_with_subject = bool(re.match(r"^(I|you|we|they|he|she|it)\b", rest, re.I))
        is_subject_wh = wh_match.start() == 0 and not starts_with_subject

        if is_subject_wh:
            return f"{cap1(wh)} {rest}?"

        aux_match = re.match(r"^(\S+(?:\s+\S+)?)\s+(can|cannot|should|must|is|are|am|will)\s*(.*)$", rest, re.I)
        if aux_match:
            subj, aux, tail = aux_match.groups()
            result = f"{cap1(wh)} {aux.lower()} {subj_lower(subj)}{(' ' + tail) if tail else ''}?"
            return re.sub(r"\s+", " ", result)

        bare_subj = re.match(r"^(I|you|we|they|he|she|it)$", rest, re.I)
        if bare_subj:
            subj = bare_subj.group(1).lower()
            cop = "am" if subj == "i" else ("are" if subj in ("you", "we", "they") else "is")
            return f"{cap1(wh)} {cop} {'I' if subj == 'i' else subj}?"

        sv_match = re.match(r"^(I|you|we|they|he|she|it|[A-Za-z]+)\s+(.*)$", rest, re.I)
        if sv_match:
            subj, tail = sv_match.groups()
            aux = "does" if re.match(r"^(he|she|it)$", subj, re.I) else "do"
            tail_fixed = undo3sg(tail) if aux == "does" else tail
            result = f"{cap1(wh)} {aux} {subj_lower(subj)} {tail_fixed}?"
            return re.sub(r"\s+", " ", result)

        return f"{cap1(wh)} {rest}?"

    aux_match = re.match(r"^(\S+(?:\s+\S+)?)\s+(can|cannot|should|must|is|are|am|will)\s+(.*)$", s, re.I)
    if aux_match:
        subj, aux, rest = aux_match.groups()
        return f"{cap1(aux)} {subj_lower(subj)} {rest}?"

    sv_match = re.match(r"^(I|you|we|they|he|she|it|[A-Za-z]+)\s+(.*)$", s, re.I)
    if sv_match:
        subj, rest = sv_match.groups()
        aux = "Does" if re.match(r"^(he|she|it)$", subj, re.I) else "Do"
        rest_fixed = undo3sg(rest) if aux == "Does" else rest
        return f"{aux} {subj_lower(subj)} {rest_fixed}?"

    return s + "?"


@dataclass
class TranslationResult:
    readings: list[str]
    note: str | None = None


def translate_one_sentence(text: str, max_readings: int = 12) -> TranslationResult:
    parsed = parse_toki_pona(text)
    if parsed.error:
        return TranslationResult([], parsed.error)

    context = parsed.context
    conjunction = parsed.conjunction
    imperative = parsed.imperative
    optative = parsed.optative
    is_question = parsed.is_question
    subjects = parsed.subjects
    predicates = parsed.predicates
    corrections = parsed.corrections

    subj = subject_string(subjects, parsed.subj_is_short)

    # A "la" context clause may be a noun phrase ("tenpo pini la" = "in the
    # past") or a full clause ("mi lape la" = "when I sleep"); detect the
    # latter by a predicate marker or a pronoun-subject + verb pattern.
    ctx_prefix = ""
    if context:
        looks_clausal = "li" in context or (
            context[0] in ("mi", "sina") and len(context) >= 2 and has_role(context[1], "v")
        )
        if looks_clausal:
            inner = translate_one_sentence(" ".join(context), 1)
            inner_str = re.sub(r"[.!?]$", "", inner.readings[0] if inner.readings else "")
            ctx_prefix = f"when {lower_first(inner_str)}, " if inner_str else ""
        else:
            ctx_parsed = parse_phrase(context, 0, frozenset())
            ctx_str = realize_np(ctx_parsed, 1)[0] if ctx_parsed else ""
            if re.match(r"^⟦[^⟧]+⟧$", ctx_str):
                ctx_prefix = f"{ctx_str} "
            else:
                ctx_prefix = f"given {ctx_str}, "

    subj_variants = subj.variants if subj.variants else [SubjectVariant("", "is", False)]

    seen: set[str] = set()
    readings: list[str] = []

    for variant in subj_variants:
        v_copula = "is" if imperative else variant.copula
        pred_lists = [realize_predicate(p, variant.plural, 3, v_copula, imperative) for p in predicates]
        combos = bounded_product(pred_lists, max_readings) if predicates else [[]]
        subj_text = variant.text

        reached_cap = False
        for combo in combos:
            if optative and subj_text:
                pred_text = ", and ".join(combo)
                is_pronoun_subj = bool(re.match(r"^(I|you|we|they|he|she|it)\b", subj_text, re.I))
                if is_pronoun_subj:
                    sentence = f"{subj_text} should {strip_command(pred_text)}"
                else:
                    sentence = f"{subj_text}, {pred_text if pred_text.endswith('!') else pred_text + '!'}"
            elif imperative:
                body_text = ", and ".join(combo)
                sentence = body_text if body_text.endswith("!") else f"{body_text}!"
            elif subj_text:
                pred_text = ", and ".join(combo)
                sentence = f"{subj_text} {pred_text}"
            else:
                sentence = ", and ".join(combo)

            sentence = (ctx_prefix + sentence).strip()
            if is_question:
                sentence = to_question(sentence)
            sentence = sentence[:1].upper() + sentence[1:]
            if conjunction:
                sentence = f"{cap1(conjunction)}, {lower_first(sentence)}"
            if sentence not in seen:
                seen.add(sentence)
                readings.append(sentence)
            if len(readings) >= max_readings:
                reached_cap = True
                break
        if reached_cap:
            break

    corr_note = (
        "Corrected: " + ", ".join(f"{c.from_} → {c.to}" for c in corrections) + "."
        if corrections
        else None
    )

    # No predicate (just a noun phrase): gloss the phrase itself.
    if not predicates and subjects:
        np_readings = realize_np(subjects[0], max_readings)
        note_parts = [p for p in (corr_note, "No predicate — glossed as a noun phrase.") if p]
        return TranslationResult([cap1(r) for r in np_readings[:max_readings]], " ".join(note_parts))

    return TranslationResult(readings, corr_note)


def translate_to_english(text: str, max_readings: int = 12) -> TranslationResult:
    sentences = segment_sentences(text)
    if not sentences:
        return TranslationResult([], "Nothing to translate.")

    if len(sentences) == 1:
        return translate_one_sentence(sentences[0], max_readings)

    # Multiple sentences: show the top reading of each sentence joined into a
    # passage, plus a few alternates swapping in a secondary reading at a time
    # (full cross-product would explode combinatorially).
    per_sentence = [translate_one_sentence(s, max_readings) for s in sentences]
    notes = [r.note for r in per_sentence if r.note]

    def join_passage(parts: list[str]) -> str:
        return ". ".join(re.sub(r"[.!]$", "", s) for s in parts) + "."

    primary = join_passage([r.readings[0] if r.readings else "(…)" for r in per_sentence])
    readings = [primary]

    for depth in range(1, 3):
        if len(readings) >= max_readings:
            break
        for i in range(len(per_sentence)):
            if len(readings) >= max_readings:
                break
            alts = per_sentence[i].readings
            if depth >= len(alts):
                continue
            passage = join_passage([
                alts[depth] if j == i else (per_sentence[j].readings[0] if per_sentence[j].readings else "(…)")
                for j in range(len(per_sentence))
            ])
            if passage not in readings:
                readings.append(passage)

    note = " ".join(notes) if notes else f"{len(sentences)} sentences."
    return TranslationResult(readings, note)
