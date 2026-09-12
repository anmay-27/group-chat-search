"""Fixed, manually authored relevance labels, never imported by search.py."""


def make_queries(targets):
    # These eight English paraphrases have no word tokens in common with targets.
    hard = [
        ("When did everyone settle on the holiday destination?", "trip"),
        ("Which vacation location won after all the debating?", "trip"),
        ("Where was our getaway eventually approved?", "trip"),
        ("What lodging arrangement did everyone agree upon?", "budget"),
        ("Which overnight accommodation received collective approval?", "budget"),
        ("How much was the agreed nightly stay allowance?", "budget"),
        ("When will students present their working invention?", "event"),
        ("Which schedule was approved for showcasing our creation?", "event"),
    ]
    semantic = [
        ("When did we decide where to go?", "trip"),
        ("When did we finally choose our destination?", "trip"),
        ("kab final hua tha kidhar jana hai?", "trip"),
        ("Manali locked kab hua?", "trip"),
        ("rehne ka kya final hua?", "budget"),
        ("Did we finalize a hostel for 2500 per person?", "budget"),
        ("What was the final project demonstration date?", "event"),
        ("prototype kab dikhayenge?", "event"),
        ("Where were the missing keys found?", "keys"),
        ("Where can I collect the laptop charger?", "charger"),
        ("Which cake was ordered for the birthday?", "cake"),
        ("What time and platform does our train leave from?", "train"),
        ("Who packed bandages for emergencies?", "medicine"),
        ("Does anyone have a spare umbrella?", "umbrella"),
    ]
    person = [
        ("What did Priya say about our budget?", "priya_budget"),
        ("Priya ne paiso ko leke kya bola tha?", "priya_budget"),
        ("What is Priya's maximum spending limit?", "priya_budget"),
        ("What did Rahul confirm about Manali?", "trip"),
        ("What did Simran suggest booking for 2500?", "budget"),
        ("What date did Neha confirm for the prototype?", "event"),
        ("Where did Riya find her keys?", "keys"),
        ("Where did Arjun leave the charger?", "charger"),
        ("What did Priya say about the bus refund?", "refund"),
        ("When is Aman's dentist appointment?", "dentist"),
    ]
    time = [
        ("What did we discuss in February about our destination?", "trip"),
        ("What accommodation did we settle on in April?", "budget"),
        ("What did we discuss last month?", "event"),
        ("What did Priya say about refunds in May?", "refund"),
        ("What exam room changed last week?", "exam"),
        ("What payment was made yesterday?", "rent"),
        ("What food did we order today?", "pizza"),
        ("Where is the spare umbrella this month?", "umbrella"),
    ]
    items = [{"query": q, "target_message_id": targets[t], "category": "semantic",
              "zero_word_overlap": True} for q, t in hard]
    for category, examples in [("semantic", semantic), ("person", person), ("time", time)]:
        items.extend({"query": q, "target_message_id": targets[t], "category": category}
                     for q, t in examples)
    assert len(items) == 40
    return items
