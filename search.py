"""Text embeddings plus optional sender/calendar filters. No query-specific rules."""
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import json
import re
import numpy as np
import pandas as pd
from build_index import DATA_DIR, MODEL_NAME, ROOT

MONTHS = {name.lower(): number for number, name in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"], 1)}


@lru_cache(maxsize=1)
def load_index():
    path = DATA_DIR / "chat.csv"
    manifest = json.loads((DATA_DIR / "index.json").read_text(encoding="utf-8"))
    if manifest["model"] != MODEL_NAME or manifest["chat_sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
        raise ValueError("Chat or model changed. Run python build_index.py, then restart the app.")
    chat = pd.read_csv(path, parse_dates=["timestamp"], keep_default_na=False)
    embeddings = np.load(DATA_DIR / "embeddings.npy", allow_pickle=False)
    if (chat.message_id.tolist() != manifest["message_ids"]
            or list(embeddings.shape) != manifest["shape"]
            or embeddings.shape[0] != len(chat)):
        raise ValueError("Index rows do not match chat. Run python build_index.py.")
    from sentence_transformers import SentenceTransformer

    return chat, embeddings, SentenceTransformer(MODEL_NAME, cache_folder=str(ROOT / ".model_cache"))


def parse_filters(query, participants, reference_date):
    """Ranges are inclusive-start/exclusive-end, relative to latest chat day."""
    sender = next((name for name in participants
                   if re.search(rf"\b{re.escape(name)}\b", query, re.I)), None)
    today = pd.Timestamp(reference_date).to_pydatetime().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end = None
    match = re.search(r"\b(today|yesterday|last week|last month|this month)\b", query, re.I)
    if match:
        phrase = match.group().lower()
        if phrase == "today":
            start, end = today, today + timedelta(days=1)
        elif phrase == "yesterday":
            start, end = today - timedelta(days=1), today
        elif phrase == "last week":
            end = today - timedelta(days=today.weekday())
            start = end - timedelta(days=7)
        elif phrase == "last month":
            end = today.replace(day=1)
            start = (end - timedelta(days=1)).replace(day=1)
        else:
            start = today.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1)
    else:
        for name, month in MONTHS.items():
            match = re.search(rf"\b{name}\b(?:\s+(\d{{4}}))?", query, re.I)
            if match:
                year = int(match.group(1)) if match.group(1) else today.year - (month > today.month)
                start = datetime(year, month, 1)
                end = datetime(year + (month == 12), month % 12 + 1, 1)
                break
    return sender, start, end


def semantic_query(query, sender, has_date):
    """Remove recognized metadata and common question framing, keeping the topic."""
    if not sender and not has_date:
        return query.strip()
    text = query.strip()
    if sender:
        name = re.escape(sender)
        text = re.sub(rf"^what did {name} (?:say|mention|tell us)(?: about| regarding)?\s*", "", text, flags=re.I)
        text = re.sub(rf"\b{name}\b(?:\s+ne\b)?", "", text, flags=re.I)
        text = re.sub(r"\bkya bola tha\b", "", text, flags=re.I)
    if has_date:
        months = "|".join(MONTHS)
        text = re.sub(rf"\b(?:(?:in|during)\s+)?(?:today|yesterday|last week|last month|this month|(?:{months})(?:\s+\d{{4}})?)\b", "", text, flags=re.I)
    text = " ".join(text.split()).strip(" ?.,")
    return text or query.strip()


def search_chat(query, top_k=5):
    if not isinstance(query, str) or not query.strip():
        return []
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")
    chat, embeddings, model = load_index()
    sender, start, end = parse_filters(query, chat.sender.unique(), chat.timestamp.max())
    mask = np.ones(len(chat), dtype=bool)
    if sender:
        mask &= chat.sender.eq(sender).to_numpy()
    if start is not None:
        mask &= ((chat.timestamp >= start) & (chat.timestamp < end)).to_numpy()
    candidates = np.flatnonzero(mask)
    if not len(candidates):
        return []
    query_embedding = model.encode(semantic_query(query, sender, start is not None), normalize_embeddings=True)
    # Dot product equals cosine similarity because both sides are normalized.
    scores = embeddings[candidates] @ query_embedding
    order = np.argsort(-scores, kind="stable")
    # Repeated replies should not occupy all five result slots. Keep the best
    # occurrence and its original chronological context, without changing scores.
    keys = chat.iloc[candidates].text.str.casefold().str.split().str.join(" ")
    counts = keys.value_counts()
    seen = set()
    results = []
    for position in order:
        key = keys.iloc[int(position)]
        if key in seen:
            continue
        seen.add(key)
        row_index = int(candidates[position])
        row = chat.iloc[row_index]
        context = chat.iloc[max(0, row_index - 2):row_index + 3].copy()
        context["timestamp"] = context.timestamp.dt.strftime("%Y-%m-%d %H:%M:%S")
        results.append({
            "message_id": int(row.message_id),
            "timestamp": row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "sender": row.sender, "text": row.text, "score": float(scores[position]),
            "occurrences": int(counts[key]),
            "context": context.to_dict("records"),
        })
        if len(results) == top_k:
            break
    return results
