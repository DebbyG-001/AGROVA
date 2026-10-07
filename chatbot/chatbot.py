import os
import sys
import json
import re
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from knowledge.retriever import retriever, detect_query_species
except ImportError:
    retriever = None

    def detect_query_species(query: str) -> set:  # retriever unavailable: no species filtering
        return set()

try:  # imported as a package (FastAPI: chatbot.chatbot)
    from .lang_utils import is_pidgin, conversation_is_pidgin
    from .record_logging import handle_logging
    from .local_responder import local_reply, RECORD_SPECIES_GROUP
except ImportError:  # run as a script (python chatbot/chatbot.py)
    from lang_utils import is_pidgin, conversation_is_pidgin
    from record_logging import handle_logging
    from local_responder import local_reply, RECORD_SPECIES_GROUP

# Load .env from root or backend
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / "backend" / ".env")
load_dotenv()


# In-memory session store for multi-turn chats
SESSION_STORE: Dict[str, List[Dict[str, str]]] = {}
MAX_HISTORY_MESSAGES = 12  # last 6 farmer/assistant exchanges are sent to the model

def find_sqlite_db() -> Path:
    """Return the same database file the FastAPI backend uses (backend/agrova.db).

    Set AGROVA_DB_PATH to point somewhere else (used by the self-test so it never touches real data).
    """
    override = os.getenv("AGROVA_DB_PATH")
    return Path(override) if override else ROOT_DIR / "backend" / "agrova.db"

def fetch_farmer_records(farmer_id: int = 1) -> Dict[str, Any]:
    """Fetch animals, health events, and feed records directly from SQLite DB."""
    farm_context = {"animals": [], "health_events": [], "feed_records": [], "production_records": []}
    db_path = find_sqlite_db()
    
    if not db_path.exists():
        return farm_context

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT id, species, breed, age_days, batch, notes FROM animals WHERE farmer_id = ?", (farmer_id,))
        farm_context["animals"] = [dict(row) for row in cur.fetchall()]

        # Records are scoped to this farmer's animals via a join, so one farmer never sees another's data.
        cur.execute(
            "SELECT h.animal_id, h.date, h.symptom, h.diagnosis, h.treatment, h.notes "
            "FROM health_events h JOIN animals a ON a.id = h.animal_id "
            "WHERE a.farmer_id = ? ORDER BY h.date DESC LIMIT 20",
            (farmer_id,),
        )
        farm_context["health_events"] = [dict(row) for row in cur.fetchall()]

        cur.execute(
            "SELECT f.animal_id, f.date, f.feed_type, f.quantity_kg, f.cost, f.notes "
            "FROM feed_records f JOIN animals a ON a.id = f.animal_id "
            "WHERE a.farmer_id = ? ORDER BY f.date DESC LIMIT 20",
            (farmer_id,),
        )
        farm_context["feed_records"] = [dict(row) for row in cur.fetchall()]

        cur.execute(
            "SELECT p.animal_id, p.date, p.metric, p.amount, p.notes "
            "FROM production_records p JOIN animals a ON a.id = p.animal_id "
            "WHERE a.farmer_id = ? ORDER BY p.date DESC LIMIT 20",
            (farmer_id,),
        )
        farm_context["production_records"] = [dict(row) for row in cur.fetchall()]

        conn.close()
    except Exception as e:
        print(f"[Farm DB Access Notice] {e}")

    return farm_context

def _short(text: Any, limit: int = 110) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"

def format_farm_context(
    farm_data: Dict[str, Any],
    species_groups: Optional[set] = None,
    max_health: int = 10,
    max_feed: int = 6,
    max_production: int = 8,
) -> str:
    """Compact text version of the farmer's records (keeps the prompt small).

    If the farmer asked about a particular animal, only that animal's records are listed in detail.
    """
    animals = farm_data.get("animals", [])
    if not animals:
        return "No farm records found for this farmer."

    relevant_ids = {a["id"] for a in animals}
    if species_groups:
        matching = {a["id"] for a in animals if RECORD_SPECIES_GROUP.get(a.get("species")) in species_groups}
        if matching:
            relevant_ids = matching
    batch_of = {a["id"]: a.get("batch") or f"animal {a['id']}" for a in animals}

    lines = ["ANIMALS:"]
    for a in animals:
        lines.append(f"- {a['batch']} | {a['species']} | {a.get('breed') or 'breed n/a'} | {a.get('age_days') or '?'} days old")

    def section(title: str, rows: list, fields: list, limit: int):
        picked = [r for r in rows if r["animal_id"] in relevant_ids][:limit]
        if not picked:
            return
        lines.append(f"{title} (latest first):")
        for r in picked:
            parts = [f"{k}: {_short(r[k])}" for k in fields if r.get(k) not in (None, "")]
            lines.append(f"- {r['date']} [{batch_of[r['animal_id']]}] " + "; ".join(parts))

    section("HEALTH EVENTS", farm_data.get("health_events", []), ["symptom", "diagnosis", "treatment", "notes"], max_health)
    section("FEED RECORDS", farm_data.get("feed_records", []), ["feed_type", "quantity_kg", "cost", "notes"], max_feed)
    section("PRODUCTION RECORDS", farm_data.get("production_records", []), ["metric", "amount", "notes"], max_production)
    return "\n".join(lines)

def build_system_prompt(user_in_pidgin: bool) -> str:
    if user_in_pidgin:
        tone_instruction = (
            "The farmer is speaking in Nigerian Pidgin. YOU MUST RESPOND IN NATURAL, WARM NIGERIAN PIDGIN "
            "(e.g., 'I hear you well', 'From your farm record for Batch B17...', 'Wetin you need do sharp-sharp...', "
            "'Make you check...', 'Abeg make vet check am too'). Keep it practical, empathetic, and clear."
        )
    else:
        tone_instruction = (
            "Respond in clear, accessible, and friendly English suitable for an African livestock farmer."
        )

    return (
        "You are AGROVA, an intelligent AI farm assistant and decision-support engine for African farmers.\n"
        f"{tone_instruction}\n\n"
        "GUIDELINES:\n"
        "1. Maintain multi-turn conversational context. Reference prior messages when the farmer provides follow-up answers.\n"
        "2. Combine the verified Agricultural Knowledge (FAO/veterinary manuals) with the farmer's Farm Records.\n"
        "3. Pinpoint probable causes (e.g. Coccidiosis, Heat Stress, Feed formulation issues).\n"
        "4. Provide immediate, safe management steps (e.g. dry litter, electrolytes, approved anticoccidials).\n"
        "5. SAFETY: Never state a 100% absolute diagnosis. Always encourage local veterinary guidance.\n"
        "6. GROUNDING: Take disease facts, signs and control steps ONLY from the AUTHORITATIVE KNOWLEDGE BASE EXCERPTS. "
        "If they do not cover the question, say so plainly and advise a vet instead of guessing. "
        "Briefly name the source (e.g. 'FAO/ILCA review') when you use a fact.\n"
        "7. SPECIES: Only discuss the animal the farmer asked about. Never apply a disease from another species "
        "(for example, do not mention Newcastle disease for goats or pigs).\n"
        "8. FARM RECORDS: Only mention record details (batch names, counts, dates) that appear in FARMER'S CURRENT DATABASE "
        "RECORDS. Never invent animal IDs or numbers.\n"
        "9. NO INVENTED DOSES OR RECIPES: Do not give drug doses, home-made mixtures, volumes (ml, litres), weights, "
        "percentages or amounts of any medicine, feed, fluid or supplement unless they appear in the "
        "knowledge excerpts. Say that the vet or agro-vet must give dosing. Do not suggest a cure for a disease the "
        "excerpts say has no treatment.\n"
        "10. For diseases such as PPR, ASF, FMD, lumpy skin disease or Newcastle disease, tell the farmer to isolate the animals, "
        "stop moving or selling them, and report to the state veterinary office.\n\n"
        "LANGUAGE: Follow the tone instruction above exactly. If the farmer writes Pidgin, the WHOLE reply, including the steps, "
        "must be in natural Nigerian Pidgin.\n"
        "CONSISTENCY: Stay consistent with your earlier replies in this conversation. If you already flagged a serious disease "
        "(for example PPR), do not downgrade it unless the farmer gives new information that rules it out.\n\n"
        "FORMAT (very important): The farmer reads on a small phone. Use plain text only: no tables, no markdown headings, "
        "no emojis. Keep the whole reply under about 120 words, in this shape: "
        "(1) one sentence on what it probably is and why, using their farm record if it fits; "
        "(2) 'Do now:' with 3 or 4 short numbered steps; "
        "(3) 'Call the vet if:' one line; "
        "(4) ONE follow-up question. "
        "Leave out any part that does not apply. For a greeting or a simple question about their records, answer in 1 to 3 sentences."
    )

def get_llm_client():
    """Detect available LLM provider (OpenAI, Groq, OpenRouter, or Custom Base URL)."""
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    custom_base = os.getenv("LLM_BASE_URL")
    custom_key = os.getenv("LLM_API_KEY")

    if groq_key:
        from openai import OpenAI
        return OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1"), os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    elif openrouter_key:
        from openai import OpenAI
        return OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1"), os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct")
    elif openai_key:
        from openai import OpenAI
        return OpenAI(api_key=openai_key), os.getenv("LLM_MODEL", "gpt-4o-mini")

    elif custom_base and custom_key:
        from openai import OpenAI
        return OpenAI(api_key=custom_key, base_url=custom_base), os.getenv("LLM_MODEL", "default")
    return None, None

def call_llm(
    messages: List[Dict[str, str]], 
    farm_data: Optional[Dict[str, Any]] = None,
    knowledge_results: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Send conversation to live LLM model (OpenAI / Groq / OpenRouter) or fallback locally."""
    client, model_name = get_llm_client()
    if client:
        try:
            extra = {"reasoning_effort": "low"} if "gpt-oss" in (model_name or "") else {}
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.3,
                extra_body=extra or None,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Live LLM Error] {e}. Falling back to local reasoning engine.")

    return generate_local_multiturn_response(messages, farm_data=farm_data, knowledge_results=knowledge_results)


def generate_local_multiturn_response(
    messages: List[Dict[str, str]],
    farm_data: Optional[Dict[str, Any]] = None,
    knowledge_results: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Offline answer built from the farmer's own records and the knowledge base (see local_responder.py)."""
    return local_reply(messages, farm_data=farm_data, knowledge_results=knowledge_results)


def agrova_chat(
    user_input: str, 
    farmer_id: int = 1, 
    session_id: str = "default",
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Main Multi-Turn Agrova Conversational Pipeline.
    Maintains session history across turns.
    """
    # 1. Manage Multi-turn Session History
    if history is not None:
        session_history = history
    else:
        if session_id not in SESSION_STORE:
            SESSION_STORE[session_id] = []
        session_history = SESSION_STORE[session_id]

    previous_user_msgs = [m["content"] for m in session_history if m["role"] == "user"]
    user_pidgin = conversation_is_pidgin(user_input, previous_user_msgs)

    # 1b. Live farm records for this farmer
    farm_data = fetch_farmer_records(farmer_id=farmer_id)

    # 1c. Is the farmer recording something ("I fed the broilers 40 kg today")? Handled without the LLM,
    #     and nothing is saved until the farmer confirms with YES.
    logging_reply = handle_logging(session_id, user_input, farm_data.get("animals", []), find_sqlite_db(), user_pidgin)
    if logging_reply is not None:
        session_history.append({"role": "user", "content": user_input})
        session_history.append({"role": "assistant", "content": logging_reply})
        SESSION_STORE[session_id] = session_history
        return {
            "reply": logging_reply,
            "session_id": session_id,
            "history_length": len(session_history),
            "history": session_history
        }

    # 2. Retrieve authoritative knowledge from ingested documents
    # Combine full recent conversation context for better search
    recent_context = " ".join([m["content"] for m in session_history[-2:]] + [user_input])
    knowledge_results = []
    if retriever:
        knowledge_results = retriever.retrieve(recent_context, top_k=2)
    
    # Which animal is the farmer talking about? Use this message first, then recent context
    species_groups = detect_query_species(user_input) or detect_query_species(recent_context)

    # 4. Format knowledge & farm context into system prompt
    knowledge_context = "\n\n".join([f"[{k['source']} - {k['title']}]:\n{k['content']}" for k in knowledge_results])
    system_prompt = build_system_prompt(user_pidgin)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"AUTHORITATIVE KNOWLEDGE BASE EXCERPTS:\n{knowledge_context}"},
        {"role": "system", "content": f"FARMER'S CURRENT DATABASE RECORDS:\n{format_farm_context(farm_data, species_groups)}"},
    ]
    
    # Append prior conversation turns
    # Only the most recent turns go to the model (keeps replies fast and cheap in long chats)
    for turn in session_history[-MAX_HISTORY_MESSAGES:]:
        messages.append(turn)
    
    # Last-minute reminder: models follow the most recent instruction best
    reminder = (
        "REMINDER: Plain text, under 120 words. Do NOT write any quantity for medicines, feed, fluids or supplements "
        "(no ml, mg, grams, litres or percentages) unless that exact number is in the knowledge excerpts; say the vet or "
        "agro-vet will give the dose."
    )
    if user_pidgin:
        reminder = "REMINDER: The farmer writes Pidgin, so reply fully in natural Nigerian Pidgin, not English. " + reminder
    messages.append({"role": "system", "content": reminder})

    # Append current user message
    messages.append({"role": "user", "content": user_input})
    
    # 5. Generate AI response
    reply = call_llm(messages, farm_data=farm_data, knowledge_results=knowledge_results)

    
    # 6. Update session history
    session_history.append({"role": "user", "content": user_input})
    session_history.append({"role": "assistant", "content": reply})
    SESSION_STORE[session_id] = session_history

    return {
        "reply": reply,
        "session_id": session_id,
        "history_length": len(session_history),
        "history": session_history
    }

if __name__ == "__main__":
    print("=" * 65)
    print("🌾 AGROVA MULTI-TURN AI FARM ASSISTANT (PIDGIN & RAG ACTIVE) 🌾")
    print("=" * 65)
    print("Type your message (type 'reset' to start fresh, 'exit' to quit):\n")
    
    session_id = "cli_session"
    SESSION_STORE[session_id] = []

    while True:
        try:
            user_msg = input("Farmer: ")
            if not user_msg.strip():
                continue
            if user_msg.lower() in {"exit", "quit"}:
                break
            if user_msg.lower() == "reset":
                SESSION_STORE[session_id] = []
                print("🔄 Conversation reset!\n")
                continue
            
            print("\n🤖 Agrova thinking (Multi-Turn Reasoning + Farm Context)...")
            result = agrova_chat(user_msg, session_id=session_id)
            print(f"\n{result['reply']}\n")
            print("-" * 65)
        except (KeyboardInterrupt, EOFError):
            break
