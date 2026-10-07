"""Log feed, production and health records from a chat message.

Flow: the farmer says something like "I fed the broilers 40 kg today" -> we parse it, work out which animal
batch it is about (asking if unsure), repeat it back, and only save after the farmer answers YES.
Works offline (plain parsing, no LLM) and understands simple Pidgin.
"""
import re
import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# session_id -> unfinished logging request waiting for the farmer's answer
PENDING_ACTIONS: Dict[str, Dict[str, Any]] = {}

SPECIES_WORDS: Dict[str, Set[str]] = {
    "poultry": {"chicken", "chickens", "broiler", "broilers", "layer", "layers", "bird", "birds", "fowl", "fowls",
                "hen", "hens", "egg", "eggs", "cockerel", "cockerels", "chick", "chicks"},
    "goat": {"goat", "goats", "kid", "kids", "doe", "does", "buck"},
    "sheep": {"sheep", "ram", "rams", "ewe", "ewes", "lamb", "lambs"},
    "cattle": {"cow", "cows", "cattle", "calf", "calves", "bull", "bulls", "heifer", "heifers"},
    "pig": {"pig", "pigs", "piglet", "piglets", "sow", "sows", "boar", "hog", "hogs"},
    "fish": {"fish", "fishes", "catfish", "tilapia", "pond", "ponds", "fingerling", "fingerlings"},
}

# Word in the message -> substrings to look for in the batch name / breed of an animal
NARROWING: Dict[str, List[str]] = {
    "broiler": ["broiler", "ross"], "broilers": ["broiler", "ross"],
    "layer": ["layer", "isa"], "layers": ["layer", "isa"], "egg": ["layer", "isa"], "eggs": ["layer", "isa"],
    "catfish": ["catfish", "clarias"], "tilapia": ["tilapia"],
    "sow": ["sow"], "piglet": ["piglet"], "piglets": ["piglet"], "yankasa": ["yankasa"],
}

_NUM = r"(\d+(?:\.\d+)?)"
_KG = re.compile(_NUM + r"\s*(?:kg|kgs|kilo|kilos|kilogram|kilograms)\b")
_EGGS_A = re.compile(r"(\d[\d,]*)\s*eggs?\b")
_EGGS_B = re.compile(r"\beggs?\b[^0-9\n]{0,25}?(\d[\d,]*)\b")
_LITRES = re.compile(_NUM + r"\s*(?:litres?|liters?|ltrs?|lt|l)\b")
_WEIGHT = re.compile(r"(?:weigh(?:s|ed|ing)?|weight)[^0-9]{0,25}" + _NUM + r"\s*(kg|kgs|g|gm|gram|grams)\b")
_DEAD = re.compile(r"(\d+)\s+(?:[a-z]+\s+){0,3}?(?:died|dead|die|dying|death)\b")
_LOST = re.compile(r"\b(?:lost|lose)\s+(\d+)\b")
_EXPLICIT_HEALTH = re.compile(r"^\s*(?:please\s+)?(?:log|record|note|add)\s*(?:that)?\s*[:\-]?\s*(.+)$", re.IGNORECASE)
_COST = re.compile(r"(?:₦|\bn)\s?(\d[\d,]{2,})|(\d[\d,]{2,})\s*naira", re.IGNORECASE)

_FEED_VERB = re.compile(r"\b(?:fed|feed|feeding|gave|give|given|giving|used|use|served|chop|poured)\b")
_NOT_USE = re.compile(r"\b(?:bought|buy|purchase|purchased|sold|sell|sale|price)\b")
_HEALTH_WORD = re.compile(
    r"sick|cough|diarrh|stool|dying|died|dead|weak|limp|lump|swell|bleed|fever|vaccin|dewor|treat|medic|inject|"
    r"not eating|no dey chop|dey die|gasp|pale|thin|wound|lame|abort|born|farrow|kidd|lamb|calv", re.IGNORECASE)
_FEED_NAMES = ["layer mash", "grower mash", "starter", "grower", "finisher", "pellets", "pellet", "mash",
               "concentrate", "hay", "silage", "cassava peels", "cassava", "browse", "bran", "maize",
               "cottonseed cake", "groundnut cake", "cake"]

_YES = re.compile(
    r"^\s*(?:yes|yeah|yep|yup|y|ok|okay|sure|confirm|confirmed|correct|right|save|save it|go ahead|do it|"
    r"e correct|na so|na correct|oya|abeg do am)(?:\s+(?:abeg|please|o|na))?\s*[.!]*\s*$", re.IGNORECASE)
_NO = re.compile(
    r"^\s*(?:abeg\s+)?(?:no|nope|n|cancel|stop|wrong|no be so|leave am|forget it|don'?t save)\s*[.!]*\s*$",
    re.IGNORECASE)


def is_yes(text: str) -> bool:
    return bool(_YES.match(text or ""))


def is_no(text: str) -> bool:
    return bool(_NO.match(text or ""))


def _to_float(s: str) -> float:
    return float(s.replace(",", ""))


def score_animals(text: str, animals: List[Dict[str, Any]], extra_tokens: Optional[Set[str]] = None):
    """Rank animals by how well they match the words in the message. Returns [(score, animal), ...] best first."""
    tokens = set(re.findall(r"[a-z0-9]+", text.lower())) | (extra_tokens or set())
    scored = []
    for a in animals:
        score = 0
        if tokens & SPECIES_WORDS.get(a.get("species", ""), set()):
            score += 3
        label = f"{a.get('batch') or ''} {a.get('breed') or ''}".lower()
        label_tokens = set(re.findall(r"[a-z0-9]+", label))
        for word, subs in NARROWING.items():
            if word in tokens and any(s in label for s in subs):
                score += 3
        for code in tokens & label_tokens:
            if re.fullmatch(r"[a-z]\d{1,3}", code):  # batch codes such as b17, l03, g1, c1
                score += 5
        scored.append((score, a))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def resolve_animal(text: str, animals: List[Dict[str, Any]], extra_tokens: Optional[Set[str]] = None):
    """Returns (animal, candidates). animal is set when exactly one is clearly the best match."""
    if not animals:
        return None, []
    if len(animals) == 1:
        return animals[0], animals
    scored = score_animals(text, animals, extra_tokens)
    best = scored[0][0]
    if best <= 0:
        return None, animals
    top = [a for s, a in scored if s == best]
    return (top[0], top) if len(top) == 1 else (None, top)


def _parse_date(low: str, today: datetime.date) -> datetime.date:
    if re.search(r"\b(?:yesterday|yest|last night)\b", low):
        return today - datetime.timedelta(days=1)
    return today


def parse_log_request(text: str, animals: List[Dict[str, Any]], today: Optional[datetime.date] = None) -> Optional[Dict[str, Any]]:
    """Turn a chat message into a draft record, or None if the message is not a record to log."""
    today = today or datetime.date.today()
    if not text or "?" in text:
        return None
    low = text.lower().strip()
    if _NOT_USE.search(low):
        return None
    when = _parse_date(low, today)
    extra: Set[str] = set()
    kind = fields = summary = None

    m_egg = _EGGS_A.search(low) or _EGGS_B.search(low)
    m_milk = _LITRES.search(low) if "milk" in low else None
    m_weight = _WEIGHT.search(low)
    m_kg = _KG.search(low)
    m_dead = _DEAD.search(low) or _LOST.search(low)

    if m_egg and not m_kg:
        n = _to_float(m_egg.group(1))
        if not (0 < n <= 1_000_000):
            return None
        kind, fields, summary = "production", {"metric": "eggs", "amount": n}, f"{n:g} eggs"
        extra = {"eggs"}
    elif m_milk:
        n = _to_float(m_milk.group(1))
        if not (0 < n <= 1000):
            return None
        kind, fields, summary = "production", {"metric": "milk_liters", "amount": n}, f"{n:g} litres of milk"
        extra = {"cow"} if not (set(re.findall(r"[a-z]+", low)) & (SPECIES_WORDS["goat"] | SPECIES_WORDS["sheep"])) else set()
    elif m_weight and (set(re.findall(r"[a-z]+", low)) & SPECIES_WORDS["fish"]):
        n = _to_float(m_weight.group(1))
        grams = n * 1000 if m_weight.group(2).startswith("k") else n
        if not (1 <= grams <= 20000):
            return None
        kind, fields, summary = "production", {"metric": "avg_weight_g", "amount": grams}, f"average weight {grams:g} g"
    elif m_kg and _FEED_VERB.search(low) and not re.search(r"\bweigh", low):
        qty = _to_float(m_kg.group(1))
        if not (0 < qty <= 50000):
            return None
        feed_type = next((f for f in _FEED_NAMES if f in low), None)
        cost_m = _COST.search(low)
        cost = _to_float(cost_m.group(1) or cost_m.group(2)) if cost_m else None
        kind = "feed"
        fields = {"quantity_kg": qty, "feed_type": feed_type, "cost": cost}
        summary = f"{qty:g} kg of {feed_type or 'feed'}" + (f" (cost {cost:,.0f} naira)" if cost else "")
    elif m_dead:
        n = int(m_dead.group(1))
        if not (0 < n <= 100000):
            return None
        kind = "health"
        fields = {"symptom": f"{n} died", "notes": "Reported through chat"}
        summary = f"{n} animals died"
    else:
        m_exp = _EXPLICIT_HEALTH.match(text)
        if m_exp and _HEALTH_WORD.search(m_exp.group(1)):
            note = " ".join(m_exp.group(1).split())[:200]
            kind, fields, summary = "health", {"symptom": note, "notes": "Reported through chat"}, f"health note: {note}"

    if not kind:
        return None
    animal, candidates = resolve_animal(text, animals, extra)
    return {"kind": kind, "fields": fields, "summary": summary, "date": when.isoformat(),
            "animal": animal, "options": candidates if animal is None else []}


def _animal_label(a: Dict[str, Any]) -> str:
    return a.get("batch") or f"animal {a.get('id')}"


def _confirm_text(p: Dict[str, Any], pidgin: bool) -> str:
    batch = _animal_label(p["animal"])
    if pidgin:
        return (f"I don hear you. I go record {p['summary']} for {batch} ({p['date']}). "
                f"Talk YES make I save am, or NO make I cancel.")
    return (f"I understood: record {p['summary']} for {batch} on {p['date']}. "
            f"Reply YES to save it, or NO to cancel.")


def _choose_text(p: Dict[str, Any], pidgin: bool) -> str:
    options = "\n".join(f"{i}) {_animal_label(a)}" for i, a in enumerate(p["options"], 1))
    if pidgin:
        return f"Which one you mean for this {p['summary']}? Reply with the number:\n{options}"
    return f"Which one is this {p['summary']} for? Reply with the number:\n{options}"


def _db_error(pidgin: bool) -> str:
    return ("E no work: I no fit save the record now. Abeg try again small time." if pidgin
            else "Sorry, I could not save that record just now. Please try again in a moment.")


def save_record(db_path: Path, p: Dict[str, Any]) -> Optional[str]:
    """Insert the confirmed record. Returns a short note about the previous record (or '' if none)."""
    animal_id = p["animal"]["id"]
    f = p["fields"]
    prev_note = ""
    conn = sqlite3.connect(str(db_path), timeout=10)
    try:
        cur = conn.cursor()
        if p["kind"] == "feed":
            cur.execute("SELECT date, quantity_kg FROM feed_records WHERE animal_id = ? AND date <= ? "
                        "AND quantity_kg IS NOT NULL ORDER BY date DESC, id DESC LIMIT 1", (animal_id, p["date"]))
            row = cur.fetchone()
            prev_note = f"{row[1]:g} kg on {row[0]}" if row else ""
            cur.execute("INSERT INTO feed_records (animal_id, date, feed_type, quantity_kg, cost, notes) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (animal_id, p["date"], f.get("feed_type"), f["quantity_kg"], f.get("cost"), "Logged through chat"))
        elif p["kind"] == "production":
            cur.execute("SELECT date, amount FROM production_records WHERE animal_id = ? AND metric = ? AND date <= ? "
                        "ORDER BY date DESC, id DESC LIMIT 1", (animal_id, f["metric"], p["date"]))
            row = cur.fetchone()
            prev_note = f"{row[1]:g} on {row[0]}" if row else ""
            cur.execute("INSERT INTO production_records (animal_id, date, metric, amount, notes) VALUES (?, ?, ?, ?, ?)",
                        (animal_id, p["date"], f["metric"], f["amount"], "Logged through chat"))
        else:
            cur.execute("INSERT INTO health_events (animal_id, date, symptom, diagnosis, treatment, notes) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (animal_id, p["date"], f["symptom"], None, None, f.get("notes")))
        conn.commit()
    finally:
        conn.close()
    return prev_note


def _saved_text(p: Dict[str, Any], prev_note: str, pidgin: bool) -> str:
    batch = _animal_label(p["animal"])
    prev = ""
    if prev_note:
        prev = f" Last record before this: {prev_note}." if not pidgin else f" Last one wey dey before: {prev_note}."
    if pidgin:
        return f"I don save am: {p['summary']} for {batch} ({p['date']}).{prev}"
    return f"Saved: {p['summary']} for {batch} on {p['date']}.{prev}"


def _cancel_text(pidgin: bool) -> str:
    return "No wahala, I no save anything." if pidgin else "OK, I did not save anything."


def handle_logging(session_id: str, text: str, animals: List[Dict[str, Any]], db_path: Path,
                   pidgin: bool, today: Optional[datetime.date] = None) -> Optional[str]:
    """Return a reply if this message is part of a record-logging exchange, else None (carry on as a normal chat)."""
    pending = PENDING_ACTIONS.get(session_id)

    if pending:
        if pending["stage"] == "choose":
            if is_no(text):
                PENDING_ACTIONS.pop(session_id, None)
                return _cancel_text(pidgin)
            pick = None
            m = re.match(r"^\s*(\d+)\b", text)
            if m and 1 <= int(m.group(1)) <= len(pending["options"]):
                pick = pending["options"][int(m.group(1)) - 1]
            else:
                pick, _ = resolve_animal(text, pending["options"])
            if pick:
                pending["animal"], pending["stage"] = pick, "confirm"
                return _confirm_text(pending, pidgin)
            pending["tries"] = pending.get("tries", 0) + 1
            if pending["tries"] >= 2:
                PENDING_ACTIONS.pop(session_id, None)
                return _cancel_text(pidgin)
            return _choose_text(pending, pidgin)

        # stage == "confirm"
        if is_yes(text):
            PENDING_ACTIONS.pop(session_id, None)
            try:
                if not Path(db_path).exists():
                    return _db_error(pidgin)
                prev_note = save_record(db_path, pending)
            except Exception as e:  # never crash the chat because of a failed write
                print(f"[Record logging error] {e}")
                return _db_error(pidgin)
            return _saved_text(pending, prev_note, pidgin)
        PENDING_ACTIONS.pop(session_id, None)
        if is_no(text):
            return _cancel_text(pidgin)
        # anything else: forget the draft (nothing was saved) and treat the message as a new one

    draft = parse_log_request(text, animals, today)
    if not draft:
        return None
    if not animals:
        return ("I no see any animal for your farm record yet, so I no fit log am." if pidgin
                else "I cannot find any animals in your farm records yet, so I cannot log that.")
    draft["tries"] = 0
    PENDING_ACTIONS[session_id] = draft
    if draft["animal"] is None:
        draft["stage"] = "choose"
        return _choose_text(draft, pidgin)
    draft["stage"] = "confirm"
    return _confirm_text(draft, pidgin)
