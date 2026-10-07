"""Language helpers: detect Nigerian Pidgin without being fooled by ordinary English words."""
import re
from typing import List

# Words that are (almost) never ordinary English: one is enough.
_STRONG = [
    r"\bdey\b", r"\bwetin\b", r"\babeg\b", r"\bwey\b", r"\bsabi\b", r"\bwahala\b", r"\buna\b",
    r"\bpikin\b", r"\boga\b", r"\bhow far\b", r"\bsharp[- ]sharp\b", r"\bna so\b", r"\be don\b",
    r"\bmake i\b", r"\babi\b", r"\bnaija\b", r"\bdem (?:dey|don|no)\b",
    r"\b(?:i|we|e|he|she|you|una) don\b(?!['’])",  # "I don give...", "e don die" (not "I don't")
    r"\b(?:cow|goat|pig|bird|animal|chicken|fowl|broiler|layer|piglet|kid|ram|ewe|sow) get\b",  # "my cow get lumps" (singular only: "cows get tired" is English)
]

# Words that are also ordinary English or short: need two different ones together.
# ("don't" must not count as "don", and "fit" or "give" alone prove nothing.)
_WEAK = [
    r"\bna\b", r"\bfit\b", r"\bdon\b(?!['’])", r"\bdem\b", r"\bchop\b", r"\bwan\b",
    r"\bcommot\b", r"\bsef\b", r"\bno get\b", r"\bi get\b",
]

_STRONG_RE = [re.compile(p, re.IGNORECASE) for p in _STRONG]
_WEAK_RE = [re.compile(p, re.IGNORECASE) for p in _WEAK]


def is_pidgin(text: str) -> bool:
    """True if this single message looks like Nigerian Pidgin."""
    if not text:
        return False
    if any(p.search(text) for p in _STRONG_RE):
        return True
    return sum(1 for p in _WEAK_RE if p.search(text)) >= 2


def conversation_is_pidgin(current: str, previous_user_messages: List[str]) -> bool:
    """Pidgin for this turn: the message itself, or a very short reply ('ok', 'two kids') after a Pidgin message."""
    if is_pidgin(current):
        return True
    if previous_user_messages and len(current.split()) <= 4:
        return is_pidgin(previous_user_messages[-1])
    return False
