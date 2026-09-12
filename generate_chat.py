"""Generate a reproducible six-month group chat; no external packages needed."""
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PARTICIPANTS = ["Aman", "Priya", "Rahul", "Riya", "Vikram", "Neha", "Arjun", "Simran"]

# Small conversations keep background messages more natural than isolated random lines.
CASUAL = [
    ["kal lecture hai kya?", "haan 9 baje", "notes bhej dena plss", "done"],
    ["chai peene aa rahe?", "nhi yaar", "canteen mein samosa bhi hai", "acha", "bas 5 min"],
    ["wifi fir se gaya 😭", "router restart kr", "kiya bhai", "ab chal raha 😂"],
    ["aaj match dekha?", "last over kya tha 🔥", "haan", "<video omitted>"],
    ["assignment upload ho gaya?", "server busy aa raha", "try again after dinner", "done"],
    ["ye meme dekho 😂", "<image omitted>", "😂", "bhai bas kar"],
    ["Forwarded: campus blood donation camp on Saturday", "kahan pe?", "main gate ke paas", "okay"],
    ["lunch mein kya hai?", "rajma chawal", "nice", "mere liye bhi rakhna"],
    ["library chalna hai", "seat milegi?", "second floor khaali hai", "aa rha"],
    ["<document omitted>", "ye maths worksheet hai", "thank you!", "kal solve karte"],
    ["office se late niklunga", "traffic bhot hai", "take care", "ghar pahunch ke ping kr"],
    ["Forwarded: heavy rain advisory, carry an umbrella", "baarish shuru", "kapde andar le lo 😂", "haan"],
    ["weekend movie?", "comedy dekhte hain", "popcorn meri taraf se", "done"],
    ["good morning", "gym kaun aayega?", "aaj rest day 😂", "same"],
    ["phone ki battery dead", "charger mere bag mein hai", "mil gaya thnx", "cool"],
    ["internship form bhar diya?", "resume update krna hai", "I can review it tonight", "thanks yaar"],
]

THREADS = {
    "trip": ("2026-02-18 19:00", [
        ("Rahul", "guys chhutti mein bahar nikalte hain"),
        ("Priya", "Goa nice hai but flights mehengi hain"),
        ("Aman", "Jaipur bhi option hai, heritage dekh lenge"),
        ("Riya", "Kasol ka weather mast rahega"),
        ("Vikram", "mountains better but travel time dekho"),
        ("Neha", "beach ya pahad?"),
        ("Arjun", "Jaipur too hot hoga yaar"),
        ("Simran", "Kasol tak bus mil jayegi"),
        ("Priya", "kharcha bhi consider karo please"),
        ("Rahul", "Goa bhot expensive padega"),
        ("Aman", "overnight bus mein sab comfortable?"),
        ("Riya", "Manali bhi dekh lo, connectivity easy hai"),
        ("Vikram", "haan practical lag raha"),
        ("Neha", "poll kar lete hain"),
        ("Arjun", "Goa 2 votes, Jaipur 1, Kasol 2"),
        ("Simran", "mere exams Wednesday ko khatam"),
        ("Priya", "Thursday nikal sakte"),
        ("Rahul", "leave approve ho gayi"),
        ("Aman", "sweater le jana padega"),
        ("Riya", "weather checked, manageable hai"),
        ("Vikram", "sab apni preference bol do"),
        ("Neha", "pahad meri taraf se"),
        ("Arjun", "mere liye bhi same"),
        ("Simran", "ab aur options mat kholo"),
        ("Priya", "sab agree hain na?"),
        ("Rahul", "theek hai sabki sun li, Manali locked hai ab 😂"),
        ("Priya", "done"),
        ("Aman", "ab rooms dekhte hain"),
    ]),
    "budget": ("2026-04-12 18:00", [
        ("Aman", "ab rehne ka arrangement niptao"),
        ("Priya", "resort kaafi costly dikh raha"),
        ("Rahul", "homestay mein privacy issue hoga"),
        ("Riya", "hostel reviews decent hain"),
        ("Priya", "2500 se upar hua toh mai out hu"),
        ("Neha", "shared rooms chalega?"),
        ("Arjun", "breakfast included hona chahiye"),
        ("Simran", "ek jagah 3200 bol rahe"),
        ("Vikram", "utna nahi yaar"),
        ("Aman", "dusra option station ke paas hai"),
        ("Riya", "wahan bathrooms shared hain"),
        ("Rahul", "cleanliness reviews check karo"),
        ("Neha", "photos achhe hain but recent nahi"),
        ("Arjun", "owner se video mangwao"),
        ("Simran", "<video omitted>"),
        ("Priya", "ye theek lag raha"),
        ("Vikram", "locker milega kya?"),
        ("Aman", "haan locker aur hot water dono"),
        ("Riya", "advance kitna chahiye?"),
        ("Rahul", "aadha abhi baaki arrival pe"),
        ("Neha", "cancellation free hai 48 hours pehle"),
        ("Arjun", "breakfast bhi included confirm"),
        ("Priya", "extra charges toh nahi?"),
        ("Aman", "tax included hai"),
        ("Vikram", "toh kar do"),
        ("Simran", "final 2500 per person wala hostel book karte hain"),
        ("Priya", "haan"),
        ("Rahul", "payment kal karte hain"),
    ]),
    "event": ("2026-05-22 17:00", [
        ("Neha", "project ka demo kab rakhein?"),
        ("Arjun", "Friday ko lab free nahi"),
        ("Simran", "Saturday afternoon possible"),
        ("Vikram", "faculty ko Thursday chahiye tha"),
        ("Aman", "Monday sab available hain"),
        ("Riya", "slides tab tak polish ho jayengi"),
        ("Priya", "auditorium confirm karna padega"),
        ("Rahul", "calendar dekh ke batao"),
        ("Neha", "June mein exams bhi hain"),
        ("Arjun", "pehle week avoid karo"),
        ("Simran", "second week internship interviews"),
        ("Vikram", "last week better"),
        ("Aman", "prototype ke sensors tab aa jayenge"),
        ("Riya", "projector test karna hoga"),
        ("Priya", "main booking office jaungi"),
        ("Rahul", "poster kaun banayega?"),
        ("Neha", "main bana dungi"),
        ("Arjun", "demo live ho ya recorded?"),
        ("Simran", "live with backup video"),
        ("Vikram", "faculty ne last Monday bola"),
        ("Aman", "morning slot free hai"),
        ("Riya", "audio system bhi checked"),
        ("Priya", "hall available, written confirmation mil gayi"),
        ("Rahul", "sab apna laptop lana"),
        ("Arjun", "ab calendar mein daal do"),
        ("Neha", "29 June subah 10 baje auditorium mein apna prototype dikhayenge, pakka"),
        ("Simran", "done"),
        ("Vikram", "rehearsal ek din pehle"),
    ]),
}
# Unique everyday facts provide diverse targets beyond the three decisions.
FACTS = [
    ("dentist", "2026-01-14 12:15", "Aman", "Dentist appointment moved to 4 pm, chai later"),
    ("keys", "2026-02-05 14:00", "Riya", "Meri chabiyan library ke blue sofa ke neeche mili"),
    ("charger", "2026-03-09 11:30", "Arjun", "I left the laptop charger at the security desk"),
    ("cake", "2026-04-04 18:00", "Simran", "Neha ke birthday ke liye chocolate cake order kar diya"),
    ("train", "2026-05-09 15:00", "Vikram", "Our train leaves platform 6 at 7:40 in the evening"),
    ("refund", "2026-05-15 13:00", "Priya", "Bus cancellation ka refund aa gaya, 800 each wapas bhej rahi"),
    ("medicine", "2026-06-04 10:00", "Rahul", "First aid kit mein bandages aur antiseptic rakh diya"),
    ("umbrella", "2026-06-10 18:00", "Riya", "Extra umbrella mere backpack mein hai, baarish ho toh le lena"),
    ("exam", "2026-06-22 11:00", "Aman", "Statistics exam shifted to room B204"),
    ("rent", "2026-06-29 13:00", "Priya", "June ka flat rent transfer kar diya, receipt attached"),
    ("pizza", "2026-06-30 20:00", "Rahul", "Dinner ke liye mushroom pizza order kiya, 30 min lagenge"),
]


def build_messages():
    rng = random.Random(42)
    messages, targets = [], {}

    def add(when, sender, text, label=None):
        row = {"message_id": len(messages) + 1, "timestamp": when.strftime("%Y-%m-%d %H:%M:%S"),
               "sender": sender, "text": text}
        messages.append(row)
        if label:
            targets[label] = row

    # Six calendar months: Jan 1 through Jun 30. Bursts during waking hours.
    day = datetime(2026, 1, 1)
    for offset in range(181):
        for hour in [8, 11, 14, 17, 20, 22]:
            conversation = rng.choice(CASUAL)
            start = day + timedelta(days=offset, hours=hour, minutes=rng.randrange(20))
            for turn, text in enumerate(conversation):
                add(start + timedelta(minutes=turn * 2), rng.choice(PARTICIPANTS), text)

    for name, (start, thread) in THREADS.items():
        start = datetime.fromisoformat(start)
        # Keep these long exchanges uninterrupted for useful context.
        end = start + timedelta(minutes=3 * len(thread))
        messages = [row for row in messages if not start <= datetime.fromisoformat(row["timestamp"]) <= end]
        for turn, (sender, text) in enumerate(thread):
            add(start + timedelta(minutes=3 * turn), sender, text,
                name if turn == 25 else "priya_budget" if name == "budget" and turn == 4 else None)
    for label, when, sender, text in FACTS:
        add(datetime.fromisoformat(when), sender, text, label)

    # Reassign IDs after chronological sorting; target references follow their rows.
    messages.sort(key=lambda row: row["timestamp"])
    for number, row in enumerate(messages, 1):
        row["message_id"] = number
    return messages, {label: row["message_id"] for label, row in targets.items()}


def main():
    DATA_DIR.mkdir(exist_ok=True)
    messages, targets = build_messages()
    with (DATA_DIR / "chat.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["message_id", "timestamp", "sender", "text"])
        writer.writeheader()
        writer.writerows(messages)
    (DATA_DIR / "targets.json").write_text(json.dumps(targets, indent=2), encoding="utf-8")
    # Query definitions are kept separate from retrieval, never used for ranking.
    from query_set import make_queries
    queries = make_queries(targets)
    (DATA_DIR / "test_queries.json").write_text(
        json.dumps(queries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(messages)} messages, 8 participants, January-June 2026.")


if __name__ == "__main__":
    main()
