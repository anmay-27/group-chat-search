"""Evaluate exact target-message retrieval, including all misses."""
import json
import hashlib
from datetime import datetime, timezone
import re
from build_index import DATA_DIR, ROOT, MODEL_NAME
from search import load_index, search_chat


def summarize(rows):
    count = len(rows)
    first = sum(row["target_rank"] == 1 for row in rows)
    five = sum(row["target_rank"] is not None for row in rows)
    return {"total_queries": count, "top_1_hits": first, "top_5_hits": five,
            "top_1_accuracy": first / count if count else 0,
            "top_5_accuracy": five / count if count else 0}


def main():
    queries = json.loads((DATA_DIR / "test_queries.json").read_text(encoding="utf-8"))
    assert len(queries) == 40, "Expected exactly 40 queries."
    assert sum(q.get("zero_word_overlap", False) for q in queries) == 8
    chat, _, _ = load_index()
    messages = chat.set_index("message_id")
    rows = []
    for item in queries:
        assert item["target_message_id"] in messages.index
        if item.get("zero_word_overlap"):
            tokens = lambda text: set(re.findall(r"\b\w+\b", text.lower()))
            assert not tokens(item["query"]) & tokens(messages.loc[item["target_message_id"], "text"])
        results = search_chat(item["query"], top_k=5)
        ids = [result["message_id"] for result in results]
        rank = ids.index(item["target_message_id"]) + 1 if item["target_message_id"] in ids else None
        rows.append({**item, "target_rank": rank, "retrieved_message_ids": ids,
                     "scores": [result["score"] for result in results]})
        print(f"{len(rows):02d}/40 rank={rank}: {item['query']}", flush=True)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_NAME,
        "retrieval_method": "metadata filtering, query cleanup, cosine similarity, identical-text deduplication",
        "test_queries_sha256": hashlib.sha256((DATA_DIR / "test_queries.json").read_bytes()).hexdigest(),
        "reference_date": str(chat.timestamp.max().date()),
        "index": json.loads((DATA_DIR / "index.json").read_text(encoding="utf-8")),
        "all_queries": summarize(rows),
        "zero_word_overlap_queries": summarize([row for row in rows if row.get("zero_word_overlap")]),
        "by_category": {category: summarize([r for r in rows if r["category"] == category])
                        for category in ["semantic", "person", "time"]},
        "queries": rows,
    }
    # The full ID list is already stored in the index manifest.
    del report["index"]["message_ids"]
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    (output / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for label in ["all_queries", "zero_word_overlap_queries"]:
        stats = report[label]
        print(f"\n{label}: {stats['total_queries']} queries")
        for k in [1, 5]:
            print(f"Top-{k}: {stats[f'top_{k}_hits']}/{stats['total_queries']} = {stats[f'top_{k}_accuracy']:.1%}")


if __name__ == "__main__":
    main()
