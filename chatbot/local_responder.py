"""Offline reply engine, used when no live LLM can be reached.

It contains NO hardcoded farm data: every answer is built from the farmer's own records (passed in as
`farm_data`) and from the knowledge-base excerpts (`knowledge_results`) found for the question.
"""
import re
from typing import Any, Dict, List, Optional

try:
    from .lang_utils import conversation_is_pidgin
except ImportError:  # run as a script: python chatbot/chatbot.py
    from lang_utils import conversation_is_pidgin

try:
    from .record_logging import score_animals
except ImportError:
    from record_logging import score_animals

try:
    from knowledge.retriever import detect_query_species
except ImportError:
    def detect_query_species(query: str) -> set:
        return set()

# Farm-record species -> knowledge-base species group (see knowledge/retriever.py)
RECORD_SPECIES_GROUP = {
    "goat": "small_ruminant", "sheep": "small_ruminant", "cattle": "cattle",
    "pig": "pig", "fish": "fish", "poultry": "poultry",
}

MIN_KNOWLEDGE_SCORE = 3.0  # below this the retrieved text is probably not about the question

_GREETING = re.compile(r"^\s*(?:hi+|hello|hey|good (?:morning|afternoon|evening)|how far|wetin dey|xup|greetings|sannu)\b", re.I)
_THANKS = re.compile(r"\b(?:thank|thanks|tenki|nagode|daalu|ese|well done|good job|nice one|appreciate)\b", re.I)
_INVENTORY = re.compile(r"\b(?:how many|inventory|my animals?|my records?|my farm|show me|wetin i get|what do i have)\b", re.I)
_TREND = re.compile(r"\b(?:eggs?|milk|production|how much feed|feed records?|feed cost|feed i give|weights?|growth)\b", re.I)
_SYMPTOM = re.compile(
    r"sick|die\b|dying|dead|cough|sneez|stool|diarrh|vomit|limp|lump|swell|bleed|weak|thin\b|pale|gasp|drool|"
    r"blister|itch|scratch|wound|abort|fever|not eating|no dey (?:chop|eat)|drop|rot\b|spots?\b|paraly|twist|"
    r"pneumonia|disease|illness|problem|sore|discharge|worm|tick|mange|lame", re.I)

_FOLLOW_UPS = {
    "en": {
        "poultry": ["How many birds are affected?", "What do the droppings look like?", "Is the litter wet, and is the house very hot?"],
        "small_ruminant": ["How many animals show signs, and how old are they?", "Was any new animal brought in lately?", "Is the pen damp or crowded?"],
        "cattle": ["How many cattle show signs?", "Is there fever, lumps, drooling or lameness?", "Any new animals or contact with other herds?"],
        "pig": ["How many pigs are sick, and how old are they?", "Is there fever, red or purple skin, or sudden death?", "Have you bought or moved pigs recently?"],
        "fish": ["How many fish are affected or dead?", "What colour is the water, and when did you last feed?", "Are the fish gasping at the surface in the morning?"],
    },
    "pcm": {
        "poultry": ["How many birds dey affect?", "How the droppings look?", "The litter dey wet or the house dey too hot?"],
        "small_ruminant": ["How many animals dey show sign, and how old dem be?", "Any new animal enter your pen lately?", "The pen dey wet or crowded?"],
        "cattle": ["How many cattle dey show sign?", "E get fever, lumps, drool or limp?", "Any new animal or contact with other herd?"],
        "pig": ["How many pigs dey sick, and how old dem be?", "E get fever, red or purple skin, or sudden death?", "You don buy or move pigs lately?"],
        "fish": ["How many fish dey affect or don die?", "Wetin be the water colour, and when you last feed?", "Fish dey gasp for surface for morning?"],
    },
}


def _is_relevant(result: Dict[str, Any]) -> bool:
    """A knowledge hit counts only if it shares 2+ words with the question, or one word from its own title."""
    if result.get("relevance_score", 0) < MIN_KNOWLEDGE_SCORE:
        return False
    return len(result.get("matched_terms", [])) >= 2 or bool(result.get("title_hit"))


def _lang(pidgin: bool) -> str:
    return "pcm" if pidgin else "en"


def _animals_of(farm_data: Dict[str, Any], groups: Optional[set]) -> List[Dict[str, Any]]:
    animals = (farm_data or {}).get("animals", [])
    if not groups:
        return animals
    return [a for a in animals if RECORD_SPECIES_GROUP.get(a.get("species")) in groups]


def _trim(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "), cut.rfind(" "))
    return cut[: stop if stop > limit * 0.5 else limit].rstrip(" ,;:") + "..."


def _chunk_lines(chunk: Dict[str, Any], max_lines: int = 8, max_chars: int = 1100):
    """Turn a knowledge chunk into short readable lines plus its source label."""
    content = chunk.get("content", "")
    src = re.search(r"\(Sources?:([^)]*)\)", content)
    source = src.group(1).strip() if src else chunk.get("source", "knowledge base")
    source = re.sub(r"\s*See SOURCES\.md\.?", "", source).rstrip(" .")
    out, used = [], 0
    for i, raw in enumerate(content.splitlines()):
        line = raw.strip()
        if not line or (i == 0 and line.startswith("#")):
            continue
        if line.lower().startswith("farmer words:") or line.startswith("(Source"):
            continue
        line = re.sub(r"^#+\s*", "", line).replace("**", "")
        line = re.sub(r"^[-*]\s+", "• ", line)
        line = _trim(line)
        if used + len(line) > max_chars or len(out) >= max_lines:
            break
        out.append(line)
        used += len(line)
    return out, source


def _series(farm_data: Dict[str, Any], animals: List[Dict[str, Any]]) -> List[str]:
    """Trend lines such as 'eggs: 175 on 2026-10-03 -> 138 on 2026-10-07 (-21%)'."""
    ids = {a["id"]: a for a in animals}
    groups: Dict[tuple, list] = {}
    for r in (farm_data or {}).get("production_records", []):
        if r["animal_id"] in ids:
            groups.setdefault((r["animal_id"], r["metric"]), []).append(r)
    lines = []
    for (aid, metric), rows in groups.items():
        rows.sort(key=lambda r: r["date"])
        if len(rows) < 2:
            continue
        first, last = rows[0], rows[-1]
        pct = (last["amount"] - first["amount"]) / first["amount"] * 100 if first["amount"] else 0
        lines.append(f"{ids[aid]['batch']}: {metric.replace('_', ' ')} {first['amount']:g} on {first['date']} "
                     f"-> {last['amount']:g} on {last['date']} ({pct:+.0f}%)")
    return lines


def _narrow(animals: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """Of the animals of the right species, keep the batch(es) the message points to (layers vs broilers, goats vs sheep...)."""
    if len(animals) < 2:
        return animals
    scored = score_animals(text, animals)
    best = scored[0][0]
    return [a for s, a in scored if s == best] if best > 0 else animals


def _records_context(farm_data: Dict[str, Any], groups: Optional[set], pidgin: bool, text: str = "") -> List[str]:
    """What the farmer's own records say about the animal being discussed."""
    if not groups:
        return []
    animals = _narrow(_animals_of(farm_data, groups), text)
    if not animals:
        return []
    ids = {a["id"]: a for a in animals}
    lines = []
    events = [e for e in farm_data.get("health_events", []) if e["animal_id"] in ids]
    events.sort(key=lambda e: e["date"], reverse=True)
    if events:
        e = events[0]
        what = e.get("symptom") or "health note"
        treat = f" Treatment so far: {e['treatment']}." if e.get("treatment") else ""
        lines.append(f"{ids[e['animal_id']]['batch']}, {e['date']}: {_trim(what, 160)}.{treat}")
    lines.extend(_series(farm_data, animals))
    return lines


def _animal_list(animals: List[Dict[str, Any]]) -> str:
    return "\n".join(
        f"• {a['batch']}: {a['species']}, {a.get('breed') or 'breed not set'}, {a.get('age_days') or '?'} days old"
        for a in animals)


def _groups_for(current: str, user_msgs: List[str]) -> set:
    groups = detect_query_species(current)
    if not groups and len(user_msgs) > 1:
        groups = detect_query_species(user_msgs[-2])
    return groups


def local_reply(messages: List[Dict[str, str]], farm_data: Optional[Dict[str, Any]] = None,
                knowledge_results: Optional[List[Dict[str, Any]]] = None) -> str:
    farm_data = farm_data or {}
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    current = user_msgs[-1] if user_msgs else ""
    pidgin = conversation_is_pidgin(current, user_msgs[:-1])
    animals = farm_data.get("animals", [])
    groups = _groups_for(current, user_msgs)
    is_symptom = bool(_SYMPTOM.search(current))

    # 1. Greeting
    if _GREETING.search(current) and not is_symptom:
        if animals:
            names = ", ".join(a["batch"] for a in animals[:6]) + ("..." if len(animals) > 6 else "")
            if pidgin:
                return (f"How far! I be Agrova, your farm assistant. I see {len(animals)} group(s) for your farm: {names}.\n"
                        "You fit ask me about sickness, feeding or your records.")
            return (f"Hello! I am Agrova, your farm assistant. I can see {len(animals)} group(s) in your farm records: {names}.\n"
                    "You can ask me about sickness, feeding, housing or your records.")
        return ("How far! I no see any animal for your farm record yet. Tell me wetin you dey keep make we start."
                if pidgin else
                "Hello! I do not see any animals in your farm records yet. Tell me what you keep and we can start.")

    # 2. Thanks
    if _THANKS.search(current) and not is_symptom:
        return ("You dey welcome! Anytime you get question or you wan record something, I dey here."
                if pidgin else "You are welcome! Ask me anything about your animals, or tell me something to record.")

    # 3. Production / feed trends (only when the farmer is not reporting a sickness)
    if _TREND.search(current) and not is_symptom:
        target = _narrow(_animals_of(farm_data, groups), current) or animals
        wants_feed = bool(re.search(r"feed|chop", current, re.I))
        lines = _series(farm_data, target)
        if wants_feed or not lines:  # an egg or milk question gets production lines, not feed lines
            feeds = [f for f in farm_data.get("feed_records", []) if f["animal_id"] in {a["id"] for a in target}]
            feeds.sort(key=lambda f: f["date"], reverse=True)
            names = {a["id"]: a["batch"] for a in target}
            for f in feeds[:3]:
                if f.get("quantity_kg") is not None:
                    lines.append(f"{names[f['animal_id']]}: fed {f['quantity_kg']:g} kg of {f.get('feed_type') or 'feed'} on {f['date']}")
        if lines:
            head = "Na wetin your records show:" if pidgin else "This is what your records show:"
            tail = ("\nYou fit tell me new figures too, like 'I fed the broilers 40 kg today', I go record am after you confirm."
                    if pidgin else
                    "\nYou can also tell me new figures, like 'I fed the broilers 40 kg today', and I will record them after you confirm.")
            return head + "\n" + "\n".join(f"• {l}" for l in lines) + tail
        return ("I no see production or feed record for that yet." if pidgin
                else "I do not see production or feed records for that yet.")

    # 4. "What do I have?"
    if _INVENTORY.search(current) and not is_symptom:
        if animals:
            head = "Na your farm record be this:" if pidgin else "Here is what is in your farm records:"
            return f"{head}\n{_animal_list(animals)}"
        return ("I no see any animal for your record yet." if pidgin
                else "I do not see any animals in your records yet.")

    # 5. Knowledge-base answer
    top = (knowledge_results or [None])[0]
    if top and _is_relevant(top):
        lines, source = _chunk_lines(top)
        title = top.get("title", "Agrova knowledge base")
        parts = []
        parts.append(("Wetin my knowledge book talk about: " if pidgin else "From the Agrova knowledge base: ") + title)
        parts.append("\n".join(lines))
        mine = _records_context(farm_data, groups, pidgin, current)
        if mine:
            parts.append(("For your own record:" if pidgin else "From your own records:") + "\n" + "\n".join(f"• {l}" for l in mine))
        group = next(iter(groups), None)
        questions = _FOLLOW_UPS[_lang(pidgin)].get(group, [])
        if questions:
            parts.append(("Abeg tell me:" if pidgin else "Please tell me:") + "\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1)))
        parts.append(f"Source: {source}")
        parts.append("I cannot give a firm diagnosis or doses. Please confirm with a vet or your state veterinary office."
                     if not pidgin else
                     "I no fit give final diagnosis or dose. Abeg make vet or your state veterinary office confirm am.")
        return "\n\n".join(parts)

    # 6. Honest default
    if pidgin:
        return ("I no get reliable answer for that for my knowledge book. Tell me the animal and wetin you see "
                "(the signs, how many, how long), or ask about feeding, housing or your records. "
                "If e serious, call your vet.")
    return ("I do not have a reliable answer for that in my knowledge base. Tell me which animal it is and what you see "
            "(the signs, how many are affected, for how long), or ask about feeding, housing or your records. "
            "If it looks serious, please call your vet.")
