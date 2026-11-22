"""P3's vocabulary: which words a low-literacy or non-native reader knows.

Spec, P3: before the model sees the tree, every word outside a fixed
common-word list becomes `[unknown]`. Numbers, the site name and a short UI
allowlist are kept.

- Common words: the New General Service List 1.2 (`personas/vocab/ngsl.txt`,
  2,809 headwords). A word counts when it is a headword or a regular
  inflection of one (plural, past, -ing, comparative, -ly), or one of the
  irregular forms below. Decision recorded 22 Nov 2026 (spec: open decision
  "P3 word list").
- UI allowlist (`personas/vocab/ui_allowlist.txt`): words people see on
  almost every website (email, password, checkout), justified by Jakob's Law.

Pure functions; the perception filter `vocab_filter` applies `simplify` to
every name and text in the tree, but never to what is typed in a field.
"""

import re
from functools import cache
from pathlib import Path

VOCAB_DIR = Path(__file__).resolve().parents[1] / "personas" / "vocab"
UNKNOWN = "[unknown]"
_WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")

# Irregular forms of NGSL headwords that suffix rules cannot reach.
IRREGULAR = {
    "am": "be",
    "is": "be",
    "are": "be",
    "was": "be",
    "were": "be",
    "been": "be",
    "has": "have",
    "had": "have",
    "does": "do",
    "did": "do",
    "done": "do",
    "went": "go",
    "gone": "go",
    "made": "make",
    "said": "say",
    "got": "get",
    "took": "take",
    "taken": "take",
    "gave": "give",
    "given": "give",
    "came": "come",
    "saw": "see",
    "seen": "see",
    "knew": "know",
    "known": "know",
    "thought": "think",
    "told": "tell",
    "found": "find",
    "left": "leave",
    "felt": "feel",
    "kept": "keep",
    "brought": "bring",
    "bought": "buy",
    "sent": "send",
    "spent": "spend",
    "paid": "pay",
    "sold": "sell",
    "built": "build",
    "lost": "lose",
    "held": "hold",
    "met": "meet",
    "ran": "run",
    "wrote": "write",
    "written": "write",
    "read": "read",
    "chose": "choose",
    "chosen": "choose",
    "began": "begin",
    "begun": "begin",
    "children": "child",
    "men": "man",
    "women": "woman",
    "people": "person",
    "better": "good",
    "best": "good",
    "worse": "bad",
    "worst": "bad",
    "i": "i",
    "me": "i",
    "my": "i",
    "us": "we",
    "our": "we",
    "him": "he",
    "his": "he",
    "her": "she",
    "them": "they",
    "their": "they",
    "its": "it",
    "your": "you",
}


# Numbers are kept (spec), so number words, days, months and the currency
# name are too; NGSL leaves them out as a closed class.
NUMBERS_AND_DATES = frozenset(
    "zero one two three four five six seven eight nine ten eleven twelve twenty thirty "
    "forty fifty hundred thousand million first second third fourth fifth "
    "monday tuesday wednesday thursday friday saturday sunday january february march april "
    "may june july august september october november december rs rupee rupees an".split()
)
# Email addresses and web addresses pass through whole: a reader copies them.
_ADDRESS = re.compile(r"\S+@\S+\.\w+|https?://\S+|www\.\S+")


def _load(name: str) -> frozenset[str]:
    lines = (VOCAB_DIR / name).read_text(encoding="utf-8").splitlines()
    return frozenset(w.strip().lower() for w in lines if w.strip() and not w.startswith("#"))


@cache
def common_words() -> frozenset[str]:
    return _load("ngsl.txt")


@cache
def ui_allowlist() -> frozenset[str]:
    return _load("ui_allowlist.txt")


def _stems(word: str) -> list[str]:
    """Candidate headwords for a regular inflection of `word`."""
    out = [word]
    for suffix, repl in (
        ("ies", "y"), ("ied", "y"), ("ier", "y"), ("iest", "y"), ("ily", "y"),
        ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"), ("d", ""), ("ing", ""),
        ("ing", "e"), ("er", ""), ("er", "e"), ("est", ""), ("est", "e"), ("ly", ""),
        ("ly", "le"), ("'s", ""), ("’s", ""),
    ):  # fmt: skip
        if word.endswith(suffix) and len(word) - len(suffix) >= 2:
            stem = word[: -len(suffix)] + repl
            out.append(stem)
            # planned -> plan, stopping -> stop
            if repl == "" and len(stem) >= 3 and stem[-1] == stem[-2]:
                out.append(stem[:-1])
    return out


def known(word: str, extra: frozenset[str] = frozenset()) -> bool:
    w = word.lower()
    if w in extra or w in NUMBERS_AND_DATES:
        return True
    w = IRREGULAR.get(w, w)
    return any(s in common_words() or s in ui_allowlist() for s in _stems(w))


def simplify(text: str, extra: frozenset[str] = frozenset()) -> str:
    """`text` with every unknown word replaced by [unknown]. Numbers,
    punctuation, spacing and email or web addresses are kept, and so are
    proper nouns: a capitalised word that does not start a sentence (a name
    like "Sam Khan" or "Lahore" reads as a name, not a word to understand)."""
    out, last = [], 0
    for m in _ADDRESS.finditer(text):
        out.append(_simplify_words(text[last : m.start()], extra))
        out.append(m[0])
        last = m.end()
    out.append(_simplify_words(text[last:], extra))
    return "".join(out)


def _simplify_words(text: str, extra: frozenset[str]) -> str:
    def replace(m: re.Match) -> str:
        word = m[0]
        before = text[: m.start()].rstrip()
        starts_sentence = not before or before[-1] in ".!?:"
        if word[0].isupper() and not word.isupper() and not starts_sentence:
            return word  # a proper noun
        return word if known(word, extra) else UNKNOWN

    return _WORD.sub(replace, text)


# Function words carry no meaning of their own; a sentence of jargon joined by
# "of the" is still unreadable, so content-word shares leave them out.
FUNCTION_WORDS = frozenset(
    "a an the of to in on at by for with from upon within into onto and or but nor so "
    "if then than as be is are was were been shall will would should can could may might "
    "must do does did any all each every this that these those it its there here not no".split()
)


def unknown_share(text: str, content_only: bool = False) -> float:
    """Share of words in an already simplified text that are [unknown];
    with content_only, of the words that are not function words."""
    words = re.findall(r"\[unknown\]|[A-Za-z]+", text)
    if content_only:
        words = [w for w in words if w.lower() not in FUNCTION_WORDS]
    return sum(w == UNKNOWN for w in words) / len(words) if words else 0.0
