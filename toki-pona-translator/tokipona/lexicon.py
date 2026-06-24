"""Toki Pona lexicon: pu (the original 120 words) plus the most widely
recognized nimi ku suli (~17 extra words from Sonja Lang's "ku" survey).

Each entry maps a word to sense groups keyed by syntactic role:
    n        noun / thing
    v        verb (intransitive sense, or the only sense if untyped)
    vt       verb (transitive-specific sense, e.g. causative)
    mod      adjective / adverb / modifier
    prep     preposition
    number   numeral reading
    interj   interjection
    particle structural particle (no lexical sense; value is a tag string)
    pre-verb pre-verb / modal reading

Senses within a role are ordered most-common-first; downstream code treats
index 0 as the default gloss.
"""

from __future__ import annotations

LEXICON: dict[str, dict[str, object]] = {
    # --- particles (structural, no lexical senses) ---
    "li": {"particle": "PREDICATE"},
    "e": {"particle": "OBJECT"},
    "la": {"particle": "CONTEXT"},
    "pi": {"particle": "REGROUP"},
    "o": {"particle": "IMPERATIVE"},
    "en": {"particle": "AND_SUBJ"},
    "anu": {"particle": "OR"},

    # --- pronouns / core ---
    "mi": {"n": ["I", "me", "we", "us"], "mod": ["my", "our"]},
    "sina": {"n": ["you"], "mod": ["your"]},
    "ona": {"n": ["he", "she", "it", "they"], "mod": ["his", "her", "its", "their"]},
    "ni": {"n": ["this", "that"], "mod": ["this", "that"]},

    # --- pre-verbs ---
    "wile": {"pre-verb": ["want to", "need to", "must"], "v": ["want", "need"], "n": ["desire", "need"]},
    "ken": {"pre-verb": ["can", "be able to", "may"], "v": ["be able", "allow"], "n": ["ability", "possibility"], "mod": ["possible"]},
    "kama": {"pre-verb": ["become", "come to"], "v": ["come", "arrive", "happen"], "n": ["event", "arrival"], "mod": ["coming", "future"]},
    "awen": {"pre-verb": ["keep", "continue to"], "v": ["stay", "remain", "wait"], "n": ["endurance"], "mod": ["still", "remaining"]},
    "lukin": {"pre-verb": ["try to", "seek to"], "v": ["see", "look", "watch"], "n": ["eye", "sight"], "mod": ["visual"]},
    "alasa": {"pre-verb": ["try to"], "v": ["hunt", "search", "gather"], "n": ["hunt"]},

    # --- common content words (sense groups) ---
    "toki": {"n": ["speech", "language", "conversation", "talk"], "v": ["talk", "speak", "communicate"], "mod": ["spoken", "linguistic"], "interj": ["hello"]},
    "pona": {"mod": ["good", "simple", "positive", "friendly"], "n": ["goodness", "good", "simplicity"], "vt": ["improve", "fix", "repair"], "interj": ["great", "thanks"]},
    "ike": {"mod": ["bad", "evil", "complex", "negative"], "n": ["badness", "evil"], "vt": ["worsen", "ruin"], "interj": ["alas", "ugh"]},
    "jan": {"n": ["person", "people", "human", "somebody"], "mod": ["human", "personal"], "v": ["personify"]},
    "ijo": {"n": ["thing", "object", "matter", "something"], "mod": ["material"], "v": ["objectify"]},
    "ilo": {"n": ["tool", "device", "machine"], "mod": ["mechanical"]},
    "tomo": {"n": ["house", "home", "building", "room", "structure"], "mod": ["indoor", "domestic"], "v": ["build"]},
    "tawa": {"prep": ["to", "toward", "for"], "v": ["move", "go", "walk"], "mod": ["moving", "mobile"], "n": ["movement", "motion"]},
    "tan": {"prep": ["from", "because of"], "n": ["cause", "reason", "origin"], "v": ["originate"]},
    "lon": {"prep": ["in", "at", "on"], "v": ["exist", "be present"], "n": ["truth", "presence"], "mod": ["real", "true"]},
    "kepeken": {"prep": ["using", "with"], "v": ["use"], "n": ["use", "usage"]},
    "poka": {"prep": ["beside", "with"], "n": ["side", "hip", "vicinity"], "mod": ["nearby", "adjacent"]},
    "sama": {"prep": ["like", "as"], "mod": ["same", "similar", "equal"], "n": ["similarity", "sameness"], "v": ["resemble"]},

    "suli": {"mod": ["big", "important", "tall", "long"], "n": ["size", "importance"], "v": ["grow"], "vt": ["enlarge", "increase"]},
    "lili": {"mod": ["small", "few", "young", "short"], "n": ["smallness"], "v": ["shrink"], "vt": ["reduce", "lessen"]},
    "mute": {"mod": ["many", "much", "very"], "n": ["amount", "quantity", "many"], "number": ["many", "20"], "v": ["multiply"]},
    "ale": {"mod": ["all", "every", "complete"], "n": ["everything", "universe", "life"], "number": ["100", "infinity"]},
    "ali": {"mod": ["all", "every", "complete"], "n": ["everything", "universe"], "number": ["100"]},
    "ala": {"mod": ["no", "not", "none"], "n": ["nothing", "absence"], "number": ["zero"], "interj": ["no"]},
    "wan": {"number": ["one", "1"], "mod": ["single", "united"], "n": ["unity", "one"], "v": ["unite", "combine"]},
    "tu": {"number": ["two", "2"], "mod": ["double"], "n": ["pair"], "v": ["split", "divide"]},

    "moku": {"v": ["eat", "drink", "consume"], "n": ["food", "meal", "drink"], "mod": ["edible"]},
    "pana": {"v": ["give", "send", "emit", "release"], "n": ["gift"]},
    "jo": {"v": ["have", "hold", "carry", "contain"], "n": ["possession"]},
    "sona": {"v": ["know", "understand"], "pre-verb": ["know how to"], "n": ["knowledge", "wisdom"], "mod": ["knowledgeable"]},
    "pali": {"v": ["do", "make", "work", "build"], "n": ["work", "deed", "action"], "mod": ["active"]},
    "kalama": {"v": ["make sound", "sound"], "n": ["sound", "noise"]},
    "utala": {"v": ["fight", "battle", "struggle"], "n": ["fight", "conflict"], "mod": ["competitive"]},
    "olin": {"v": ["love", "respect"], "n": ["love", "compassion"], "mod": ["beloved"]},
    "unpa": {"v": ["have sex with"], "n": ["sex"], "mod": ["sexual"]},
    "pakala": {"v": ["break", "ruin", "harm"], "n": ["mistake", "damage"], "mod": ["broken"], "interj": ["damn"]},

    "ma": {"n": ["land", "country", "earth", "ground", "outdoors"], "mod": ["terrestrial"]},
    "telo": {"n": ["water", "liquid", "fluid"], "v": ["wash", "water"], "mod": ["wet", "liquid"]},
    "kasi": {"n": ["plant", "tree", "leaf", "herb"], "mod": ["botanical"]},
    "soweli": {"n": ["animal", "mammal", "beast"], "mod": ["animal"]},
    "waso": {"n": ["bird", "flying creature"], "mod": ["avian"]},
    "kala": {"n": ["fish", "sea creature"], "mod": ["aquatic"]},
    "pipi": {"n": ["bug", "insect", "spider"], "mod": ["insectoid"]},
    "akesi": {"n": ["reptile", "amphibian", "lizard"], "mod": ["reptilian"]},

    "suno": {"n": ["sun", "light", "brightness"], "mod": ["bright", "sunny"], "v": ["shine"]},
    "mun": {"n": ["moon", "star", "night sky object"], "mod": ["lunar"]},
    "seli": {"n": ["fire", "heat", "warmth"], "mod": ["hot", "warm"], "vt": ["heat", "cook"]},
    "lete": {"n": ["cold", "coolness"], "mod": ["cold", "cool", "raw"], "vt": ["chill", "cool"]},
    "kon": {"n": ["air", "breath", "spirit", "essence"], "mod": ["airy", "intangible"]},
    "ko": {"n": ["powder", "paste", "semi-solid", "clay"], "mod": ["powdery"]},
    "kiwen": {"n": ["stone", "metal", "hard object"], "mod": ["hard", "solid"]},

    "lipu": {"n": ["document", "paper", "page", "book", "website"], "mod": ["flat"]},
    "nimi": {"n": ["word", "name"], "v": ["name"]},
    "kulupu": {"n": ["group", "community", "society", "team"], "mod": ["collective"]},
    "nasin": {"n": ["way", "path", "method", "doctrine"], "mod": ["procedural"]},
    "open": {"v": ["open", "begin", "start"], "n": ["beginning"], "mod": ["initial"]},
    "pini": {"v": ["end", "finish", "close"], "n": ["end"], "mod": ["finished", "past"]},
    "sin": {"mod": ["new", "fresh", "another", "again"], "n": ["novelty"], "v": ["renew"]},
    "ante": {"mod": ["different", "other"], "n": ["difference", "change"], "v": ["differ"], "vt": ["change", "alter"]},
    "mama": {"n": ["parent", "mother", "father", "origin", "creator"], "mod": ["parental"]},
    "meli": {"n": ["woman", "female", "wife"], "mod": ["female", "feminine"]},
    "mije": {"n": ["man", "male", "husband"], "mod": ["male", "masculine"]},
    "jelo": {"mod": ["yellow", "golden"], "n": ["yellow"]},
    "loje": {"mod": ["red"], "n": ["red"]},
    "laso": {"mod": ["blue", "green"], "n": ["blue/green"]},
    "walo": {"mod": ["white", "light-colored"], "n": ["white"]},
    "pimeja": {"mod": ["black", "dark"], "n": ["darkness"]},
    "lawa": {"n": ["head", "mind"], "v": ["lead", "control", "govern"], "mod": ["main", "leading"]},
    "luka": {"n": ["hand", "arm"], "number": ["five", "5"], "v": ["touch"]},
    "noka": {"n": ["foot", "leg"], "mod": ["lower"], "v": ["kick", "walk"]},
    "uta": {"n": ["mouth", "lips"], "mod": ["oral"]},
    "oko": {"n": ["eye"], "mod": ["ocular"]},
    "pilin": {"v": ["feel", "think", "sense"], "n": ["feeling", "emotion", "heart"], "mod": ["emotional"]},
    "wawa": {"mod": ["strong", "powerful", "intense"], "n": ["strength", "power", "energy"], "vt": ["strengthen", "empower"]},
    "musi": {"mod": ["fun", "playful", "artful"], "n": ["game", "art", "fun"], "v": ["play", "amuse"]},
    "weka": {"mod": ["absent", "away", "gone"], "v": ["remove", "leave"], "n": ["absence"]},
    "insa": {"n": ["inside", "interior", "center", "stomach"], "mod": ["internal"], "prep": ["inside"]},
    "sewi": {"n": ["top", "sky", "height", "divinity"], "mod": ["high", "sacred", "above"]},
    "anpa": {"n": ["bottom", "ground"], "mod": ["low", "humble", "below"], "v": ["defeat"]},
    "monsi": {"n": ["back", "rear", "behind"], "mod": ["rear"]},
    "sinpin": {"n": ["face", "front", "wall"], "mod": ["frontal"]},
    "nena": {"n": ["bump", "hill", "mountain", "nose"], "mod": ["bumpy"]},
    "lupa": {"n": ["hole", "door", "opening"], "mod": ["hollow"]},
    "linja": {"n": ["line", "string", "hair", "rope"], "mod": ["long and flexible"]},
    "palisa": {"n": ["rod", "stick", "long hard thing"], "mod": ["long and stiff"]},
    "selo": {"n": ["skin", "surface", "outer layer", "shell"], "mod": ["outer"]},
    "sijelo": {"n": ["body", "physical state"], "mod": ["physical"]},
    "len": {"n": ["clothing", "cloth", "fabric", "cover"], "mod": ["covered"], "v": ["cover"]},
    "mani": {"n": ["money", "wealth", "currency", "livestock"], "mod": ["valuable"]},
    "esun": {"n": ["market", "shop", "trade"], "v": ["buy", "sell", "trade"]},
    "tenpo": {"n": ["time", "moment", "period", "occasion"], "mod": ["temporal"]},
    "poki": {"n": ["container", "box", "bowl", "cup"], "mod": ["containing"]},
    "supa": {"n": ["surface", "table", "floor", "furniture"], "mod": ["flat horizontal"]},
    "kute": {"v": ["hear", "listen", "obey"], "n": ["ear", "hearing"], "mod": ["auditory"]},
    "nasa": {"mod": ["strange", "silly", "foolish", "drunk"], "n": ["strangeness"], "vt": ["confuse", "intoxicate"]},
    "kin": {"mod": ["also", "too", "indeed"], "particle": "EMPHASIS"},
    "taso": {"mod": ["only", "sole"], "particle": "BUT", "n": ["only one"]},
    "a": {"interj": ["ah", "oh", "wow"], "particle": "EMPHASIS"},
    "mu": {"interj": ["(animal sound)", "moo", "woof"], "v": ["make animal noise"]},

    # question / deictic helpers
    "seme": {"n": ["what", "which"], "mod": ["which", "what"]},

    # --- nimi pu ---
    "jaki": {"mod": ["dirty", "gross", "disgusting", "toxic"], "n": ["filth", "waste", "garbage"], "v": ["pollute"]},
    "kili": {"n": ["fruit", "vegetable", "mushroom"], "mod": ["fruity"]},
    "kule": {"mod": ["colorful", "colored"], "n": ["color", "hue", "paint"], "v": ["color"]},
    "lape": {"v": ["sleep", "rest"], "n": ["sleep", "rest"], "mod": ["sleeping", "restful"]},
    "moli": {"v": ["die", "kill"], "n": ["death"], "mod": ["dead", "dying", "deadly"]},
    "nanpa": {"n": ["number"], "mod": ["numeric"]},
    "pan": {"n": ["bread", "grain", "cereal", "rice", "pasta"], "mod": ["starchy"]},
    "pu": {"n": ["the Toki Pona book"], "v": ["interact with the Toki Pona book"], "mod": ["pu"]},
    "sike": {"n": ["circle", "ball", "sphere", "cycle", "year"], "mod": ["round", "circular"], "v": ["circle", "orbit"]},
    "sitelen": {"n": ["image", "picture", "symbol", "writing", "drawing"], "v": ["write", "draw", "depict"], "mod": ["pictorial"]},
    "suwi": {"mod": ["sweet", "cute", "adorable"], "n": ["sweetness", "candy"], "v": ["sweeten"]},

    # --- nimi ku suli (common non-pu) ---
    "kijetesantakalu": {"n": ["raccoon", "mustelid", "procyonid"], "mod": ["raccoon-like"]},
    "tonsi": {"n": ["non-binary person", "nonbinary/trans person"], "mod": ["nonbinary"]},
    "jasima": {"v": ["reflect", "mirror", "oppose"], "n": ["mirror", "reflection"]},
    "kokosila": {"v": ["speak non-Toki-Pona in a TP setting"]},
    "lanpan": {"v": ["take", "seize", "steal"], "n": ["seizure"]},
    "meso": {"mod": ["medium", "average", "mediocre"], "n": ["middle"]},
    "misikeke": {"n": ["medicine", "remedy"], "mod": ["medicinal"], "v": ["heal"]},
    "monsuta": {"n": ["monster", "fear", "threat"], "mod": ["scary"], "v": ["fear"]},
    "n": {"interj": ["hmm", "uh"], "particle": "HESITATION"},
    "soko": {"n": ["mushroom", "fungus"], "mod": ["fungal"]},
    "namako": {"mod": ["extra", "additional", "spicy"], "n": ["spice", "addition", "extra"], "v": ["embellish"]},
    "epiku": {"mod": ["epic", "awesome", "cool"], "n": ["epicness"]},
    "kipisi": {"v": ["cut", "split", "divide"], "n": ["piece", "section"]},
    "ku": {"n": ["the Toki Pona Dictionary"], "v": ["interact with the Toki Pona Dictionary"]},
    "leko": {"n": ["block", "square", "cube", "stairs"], "mod": ["blocky", "square"]},
}

# Lexicalized compounds (collocations). Keyed by the space-joined head+modifier
# sequence. These supply the idiomatic meaning as an ADDITIONAL reading; the
# literal compositional reading is still produced separately.
# Each value lists noun (and optionally other-role) senses.
COMPOUNDS: dict[str, dict[str, list[str]]] = {
    "tomo tawa": {"n": ["vehicle", "car"]},
    "jan pona": {"n": ["friend"]},
    "jan pakala": {"n": ["criminal", "offender"]},
    "jan lawa": {"n": ["leader", "boss", "chief"]},
    "jan sewi": {"n": ["god", "deity", "priest"]},
    "jan sona": {"n": ["expert", "scholar", "wise person"]},
    "jan utala": {"n": ["soldier", "warrior", "fighter"]},
    "jan unpa": {"n": ["lover", "sexual partner"]},
    "jan toki": {"n": ["speaker", "spokesperson"]},
    "lukin oko": {"n": ["eyesight", "vision", "sight"]},
    "pilin lawa": {"n": ["intuition", "decision", "judgment"]},
    "ma tomo": {"n": ["city", "town"]},
    "tomo telo": {"n": ["bathroom", "toilet"]},
    "tomo sona": {"n": ["school"]},
    "tomo moku": {"n": ["restaurant", "kitchen"]},
    "telo nasa": {"n": ["alcohol", "liquor"]},
    "telo seli": {"n": ["hot water", "tea", "coffee"]},
    "ilo toki": {"n": ["phone", "telephone"]},
    "ilo nanpa": {"n": ["calculator", "computer"]},
    "ilo sona": {"n": ["computer"]},
    "ilo tawa": {"n": ["vehicle"]},
    "sitelen tawa": {"n": ["movie", "film", "video"]},
    "sitelen toki": {"n": ["writing", "text"]},
    "kasi kule": {"n": ["flower"]},
    "soweli lili": {"n": ["small animal", "pet"]},
    "kon pona": {"n": ["good spirit", "good mood"]},
    "pona lukin": {"mod": ["beautiful", "pretty", "good-looking"]},
    "ike lukin": {"mod": ["ugly"]},
    "nimi pona": {"n": ["compliment", "praise"]},
    "toki pona": {"n": ["Toki Pona", "the Toki Pona language"], "mod": ["simple", "good"]},
    # verb-phrase compounds (idiomatic predicates)
    "weka sona": {"v": ["forget"]},
    "weka selo": {"v": ["peel"]},
    "kama sona": {"v": ["learn", "study"]},
    "kama jo": {"v": ["get", "obtain", "receive"]},
    "kama pakala": {"v": ["get hurt", "break down", "be ruined"]},
    "lukin awen": {"v": ["watch over", "guard"]},
    "pana sona": {"v": ["teach", "inform"]},
    "telo lawa": {"n": ["shampoo"]},
    "kiwen luka": {"n": ["fingernail", "nail", "claw"]},
    "kiwen mani": {"n": ["coin"]},
    "telo loje": {"n": ["blood"]},
    "jan ike": {"n": ["enemy", "villain"]},
    # tenpo (time) expressions
    "tenpo pimeja": {"n": ["night", "nighttime"]},
    "tenpo suno": {"n": ["day", "daytime"]},
    "tenpo lape": {"n": ["bedtime", "sleep time"]},
    "tenpo mun": {"n": ["month"]},
    "tenpo sike": {"n": ["year"]},
    "tenpo esun": {"n": ["week"]},
    "tenpo pini": {"n": ["the past"], "mod": ["past", "former"]},
    "tenpo kama": {"n": ["the future"], "mod": ["future", "upcoming"]},
    "tenpo ni": {"n": ["now", "this moment"], "mod": ["current"]},
    "tenpo mute": {"mod": ["often", "frequently"], "n": ["many times"]},
    "tenpo ale": {"mod": ["always", "forever"], "n": ["all time", "eternity"]},
}

# All roles that carry lexical senses (used by reverse-index building, etc).
ROLES = ("n", "v", "vt", "mod", "prep", "number", "interj", "pre-verb")

PREVERBS = frozenset(w for w, e in LEXICON.items() if "pre-verb" in e)

# All particles, for the tokenizer/parser.
PARTICLES = frozenset(w for w, e in LEXICON.items() if "particle" in e)
