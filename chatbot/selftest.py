"""Offline self-test for the chatbot (no internet, no API key, never touches your real database).

Run from the project folder:
    backend\\.venv\\Scripts\\python.exe chatbot\\selftest.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# When run as a script, Python puts this folder first on the path, so "chatbot" would mean chatbot.py. Drop it.
sys.path = [p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]
sys.path.insert(0, str(ROOT))

# Work on a throw-away copy of the database
tmpdir = tempfile.mkdtemp(prefix="agrova_selftest_")
TEST_DB = Path(tmpdir) / "agrova_test.db"
shutil.copy(ROOT / "backend" / "agrova.db", TEST_DB)
os.environ["AGROVA_DB_PATH"] = str(TEST_DB)

from chatbot import chatbot as cb                      # noqa: E402
from chatbot.lang_utils import is_pidgin                # noqa: E402
from chatbot import record_logging as rl                # noqa: E402

# Never call a live LLM in the self-test: use the offline responder directly
cb.call_llm = lambda messages, farm_data=None, knowledge_results=None: cb.generate_local_multiturn_response(
    messages, farm_data=farm_data, knowledge_results=knowledge_results)

passed, failed = 0, []


def check(name: str, condition: bool, detail: str = ""):
    global passed
    if condition:
        passed += 1
    else:
        failed.append(f"{name}  {detail}")


def count(table: str) -> int:
    conn = sqlite3.connect(str(TEST_DB))
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def chat(msg: str, session: str = "st", farmer: int = 1) -> str:
    return cb.agrova_chat(msg, farmer_id=farmer, session_id=session)["reply"]


# ---------------------------------------------------------------- Pidgin detection
for text in ["My goat dey cough", "wetin I fit give am", "abeg help me", "How far", "the pigs na wahala",
             "my fowl dem don die", "I no sabi wetin happen", "My cow get lumps for skin", "I don give broilers 40kg"]:
    check(f"pidgin YES: {text}", is_pidgin(text))
for text in ["Can you give me advice on feeding goats?", "I don't know what to do", "That is a good fit for my farm",
             "Please give my pigs more water", "My goat has a cough", "Don't worry", "I want to chop wood",
             "Will I get a vaccine for my goats?", "The cows get tired in the heat"]:
    check(f"pidgin NO: {text}", not is_pidgin(text))

# ---------------------------------------------------------------- Parsing messages into records
animals = cb.fetch_farmer_records(1)["animals"]


def parse(text):
    return rl.parse_log_request(text, animals)


def batch(d):
    return d["animal"]["batch"] if d and d["animal"] else None


d = parse("I fed the broilers 40 kg today")
check("feed broilers", d and d["kind"] == "feed" and d["fields"]["quantity_kg"] == 40 and "B17" in batch(d), str(d))
d = parse("I don give layers 24kg mash yesterday")
check("feed layers yesterday", d and d["kind"] == "feed" and d["fields"]["feed_type"] == "mash" and "L03" in batch(d), str(d))
d = parse("I collected 150 eggs today")
check("eggs", d and d["fields"] == {"metric": "eggs", "amount": 150.0} and "L03" in batch(d), str(d))
d = parse("eggs today na 162")
check("eggs pidgin", d and d["fields"]["amount"] == 162 and "L03" in batch(d), str(d))
d = parse("got 2.5 litres of milk from the cows")
check("milk", d and d["fields"]["metric"] == "milk_liters" and "C1" in batch(d), str(d))
d = parse("catfish average weight 120 g now")
check("catfish weight", d and d["fields"]["amount"] == 120 and "C1" in batch(d), str(d))
d = parse("tilapia weigh 0.2 kg")
check("tilapia weight kg->g", d and d["fields"]["amount"] == 200 and "T1" in batch(d), str(d))
d = parse("3 broilers died today")
check("mortality", d and d["kind"] == "health" and d["fields"]["symptom"] == "3 died" and "B17" in batch(d), str(d))
d = parse("log: 2 goats dey cough and limp")
check("explicit health", d and d["kind"] == "health" and "G1" in batch(d), str(d))
d = parse("I fed my goats 20 kg cassava peels")
check("feed goats", d and d["fields"]["feed_type"] == "cassava peels" and "G1" in batch(d), str(d))
d = parse("I fed the birds 30 kg")
check("ambiguous birds", d and d["animal"] is None and len(d["options"]) == 2, str(d))
check("question not logged", parse("How many eggs should 200 layers lay?") is None)
check("purchase not logged", parse("I bought 50 kg feed") is None)
check("symptom not logged", parse("My goat dey cough") is None)
check("silly number rejected", parse("I fed the broilers 9999999 kg") is None)

# ---------------------------------------------------------------- Confirm / cancel / choose flows
feed_before = count("feed_records")
r = chat("I fed the broilers 40 kg pellets today", "log1")
check("asks to confirm", "YES" in r and "40 kg of pellets" in r and "B17" in r, r)
check("nothing saved before YES", count("feed_records") == feed_before)
r = chat("yes", "log1")
check("saved", r.startswith("Saved") and count("feed_records") == feed_before + 1, r)
conn = sqlite3.connect(str(TEST_DB))
row = conn.execute("SELECT animal_id, quantity_kg, feed_type, notes FROM feed_records ORDER BY id DESC LIMIT 1").fetchone()
conn.close()
check("saved row correct", row == (1, 40.0, "pellets", "Logged through chat"), str(row))

prod_before = count("production_records")
chat("I collected 140 eggs", "log2")
r = chat("no", "log2")
check("cancel", "did not save" in r and count("production_records") == prod_before, r)

r = chat("I fed the birds 30 kg", "log3")
check("asks which batch", "Which one" in r and "1)" in r and "2)" in r, r)
r = chat("2", "log3")
check("choice then confirm", "YES" in r, r)
chat("yes", "log3")
check("saved after choice", count("feed_records") == feed_before + 2)

r = chat("I don give goats 15kg cassava peels", "log4")
check("pidgin confirm", "YES make I save am" in r, r)
chat("abeg no", "log4")
check("pidgin cancel", count("feed_records") == feed_before + 2)

chat("I fed the broilers 10 kg", "log5")
r = chat("My goat dey cough and nose dey run", "log5")
check("other message drops draft", "Saved" not in r and count("feed_records") == feed_before + 2, r)

hev_before = count("health_events")
chat("2 piglets died today", "log6")
chat("yes", "log6")
check("mortality saved as health event", count("health_events") == hev_before + 1)

# ---------------------------------------------------------------- Offline answers built from real data
r = chat("hi", "fb1")
check("greeting uses real batches", "8 group" in r and "Herd G1" in r and "Musa" not in r, r)
r = chat("hello", "fb2", farmer=2)
check("greeting for farmer with no animals", "do not see any animals" in r, r)
r = chat("show my animals", "fb3")
check("inventory", "Pond T1" in r and "Sow S1" in r, r)
r = chat("how many eggs have my layers laid", "fb4")
check("egg trend from records", "eggs" in r and "-" in r and "L03" in r, r)
r = chat("My goat dey cough and nose dey run", "fb5")
check("goat answer from knowledge base", "PPR" in r and "Herd G1" in r and "Source" in r and "vet" in r, r)
check("source label is clean", "Source: Sources" not in r and "SOURCES.md" not in r, r)
check("no bot-directed notes", "Say losses" not in r, r)
check("goat answer does not show sheep or poultry records", "Y1" not in r and "B17" not in r, r)
r = chat("my layers egg dey drop, heat dey", "fb5b")
check("egg drop answer uses layer records only", "L03" in r and "B17" not in r and "-21%" in r, r)
r = chat("how many eggs have my layers laid", "fb5c")
check("egg trend has no feed lines", "L03" in r and "kg of" not in r and "Pellets" not in r, r)
r = chat("my pigs dey die sharp-sharp and skin dey red", "fb6")
check("pig answer", "swine fever" in r.lower(), r)
r = chat("catfish dey gasp for morning", "fb7")
check("fish answer", "oxygen" in r.lower() or "water" in r.lower(), r)
r = chat("What is the weather in Paris today", "fb8")
check("honest default", "do not have a reliable answer" in r, r)
check("no hardcoded demo numbers leak", all("48kg" not in x for x in [r]))

# ---------------------------------------------------------------- Report
shutil.rmtree(tmpdir, ignore_errors=True)
print(f"\n{passed} checks passed, {len(failed)} failed")
for f in failed:
    print("FAILED:", f[:600])
sys.exit(1 if failed else 0)
