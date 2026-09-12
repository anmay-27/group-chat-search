from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    from sentence_transformers import SentenceTransformer

    path = DATA_DIR / "chat.csv"
    chat = pd.read_csv(path, keep_default_na=False)
    if not chat.message_id.is_unique or not pd.to_datetime(chat.timestamp).is_monotonic_increasing:
        raise ValueError("Chat must have unique IDs and be sorted by timestamp.")
    model = SentenceTransformer(MODEL_NAME, cache_folder=str(ROOT / ".model_cache"))
    embeddings = model.encode(chat.text.tolist(), batch_size=64,
                              normalize_embeddings=True, show_progress_bar=True)
    np.save(DATA_DIR / "embeddings.npy", np.asarray(embeddings, dtype="float32"))
    # CSV holds sender/date/text; the manifest guarantees embedding-row alignment.
    manifest = {"model": MODEL_NAME, "chat_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "message_ids": chat.message_id.tolist(), "shape": list(embeddings.shape)}
    (DATA_DIR / "index.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Indexed {len(chat)} messages -> data/embeddings.npy")


if __name__ == "__main__":
    main()
