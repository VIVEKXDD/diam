"""
embed_and_upsert.py
-------------------
Embeds kb_documents.jsonl using BAAI/bge-base-en-v1.5 (local, free)
and upserts vectors into a Pinecone serverless index.

First run downloads the model (~400 MB) from HuggingFace — cached locally after that.

Usage
-----
    pip install pinecone sentence-transformers python-dotenv
    python embed_and_upsert.py               # full run
    python embed_and_upsert.py --dry-run     # embed only, skip upsert
    python embed_and_upsert.py --batch 50    # override upsert batch size
"""

import json
import os
import time
import argparse
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# ── Config ────────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent
KB_FILE      = SCRIPT_DIR / "kb_documents.jsonl"

MODEL_NAME   = "BAAI/bge-base-en-v1.5"
DIMENSION    = 768
METRIC       = "cosine"
EMBED_BATCH  = 64    # documents per SentenceTransformer encode call
UPSERT_BATCH = 100   # vectors per Pinecone upsert call (max 100 or 2 MB)

# BGE models use this prefix on *query* strings at inference time, not at
# indexing time — documents are embedded as-is for best retrieval performance.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


# ── Load env ──────────────────────────────────────────────────────────────────

load_dotenv(SCRIPT_DIR / ".env")

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
INDEX_NAME       = os.environ.get("PINECONE_INDEX", "diamond-kb")


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_documents(path: Path) -> list[dict]:
    docs = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def batched(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def elapsed(start: float) -> str:
    s = time.time() - start
    return f"{s:.1f}s" if s < 60 else f"{s/60:.1f}m"


# ── Embed ─────────────────────────────────────────────────────────────────────

def embed_documents(docs: list[dict]) -> list[list[float]]:
    print(f"\nLoading model: {MODEL_NAME}")
    print("  (first run downloads ~400 MB — cached after that)")
    model = SentenceTransformer(MODEL_NAME)

    texts = [doc["text"] for doc in docs]
    print(f"Embedding {len(texts)} documents in batches of {EMBED_BATCH}...")

    all_vectors = []
    t0 = time.time()

    for i, batch in enumerate(batched(texts, EMBED_BATCH)):
        vecs = model.encode(
            batch,
            normalize_embeddings=True,   # cosine similarity = dot product after L2 norm
            show_progress_bar=False,
        )
        all_vectors.extend(vecs.tolist())
        done = min((i + 1) * EMBED_BATCH, len(texts))
        print(f"  {done}/{len(texts)} embedded  [{elapsed(t0)}]")

    print(f"Embedding complete. {elapsed(t0)} total.")
    return all_vectors


# ── Pinecone ──────────────────────────────────────────────────────────────────

def get_or_create_index(pc: Pinecone) -> object:
    existing = [idx.name for idx in pc.list_indexes()]

    if INDEX_NAME in existing:
        print(f"Index '{INDEX_NAME}' already exists — connecting.")
    else:
        print(f"Creating serverless index '{INDEX_NAME}' ({DIMENSION}d, {METRIC})...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric=METRIC,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            print("  Waiting for index to be ready...")
            time.sleep(2)
        print("  Index ready.")

    return pc.Index(INDEX_NAME)


def upsert_vectors(
    index,
    docs: list[dict],
    vectors: list[list[float]],
    batch_size: int,
) -> None:
    print(f"\nUpserting {len(docs)} vectors in batches of {batch_size}...")
    t0 = time.time()

    for i, (doc_batch, vec_batch) in enumerate(
        zip(batched(docs, batch_size), batched(vectors, batch_size))
    ):
        pinecone_batch = [
            {
                "id":       doc["id"],
                "values":   vec,
                "metadata": doc["metadata"],
            }
            for doc, vec in zip(doc_batch, vec_batch)
        ]
        index.upsert(vectors=pinecone_batch)

        done = min((i + 1) * batch_size, len(docs))
        print(f"  {done}/{len(docs)} upserted  [{elapsed(t0)}]")

    print(f"Upsert complete. {elapsed(t0)} total.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Embed kb_documents.jsonl and upsert to Pinecone.")
    parser.add_argument("--dry-run",    action="store_true", help="Embed only — skip Pinecone upsert.")
    parser.add_argument("--batch",      type=int, default=UPSERT_BATCH, help=f"Upsert batch size (default {UPSERT_BATCH}).")
    parser.add_argument("--embed-only", action="store_true", help="Alias for --dry-run.")
    args = parser.parse_args()

    dry_run = args.dry_run or args.embed_only

    if not KB_FILE.exists():
        print(f"ERROR: {KB_FILE} not found. Run prepare_kb.py first.")
        raise SystemExit(1)

    if not dry_run and not PINECONE_API_KEY:
        print("ERROR: PINECONE_API_KEY not set in .env")
        raise SystemExit(1)

    # ── Load ──────────────────────────────────────────────────────────────────
    print(f"Loading documents from {KB_FILE.name}...")
    docs = load_documents(KB_FILE)

    diamond_docs = [d for d in docs if d["metadata"].get("doc_type") == "diamond_record"]
    domain_docs  = [d for d in docs if d["metadata"].get("doc_type") == "domain_knowledge"]
    print(f"  {len(docs)} total  ({len(diamond_docs)} diamond records, {len(domain_docs)} domain chunks)")

    # ── Embed ─────────────────────────────────────────────────────────────────
    vectors = embed_documents(docs)

    print(f"\nEmbedding stats:")
    print(f"  Documents : {len(vectors)}")
    print(f"  Dimensions: {len(vectors[0])}")
    print(f"  Model     : {MODEL_NAME}")

    if dry_run:
        print("\nDry run — Pinecone upsert skipped.")
        return

    # ── Upsert ────────────────────────────────────────────────────────────────
    print(f"\nConnecting to Pinecone...")
    pc    = Pinecone(api_key=PINECONE_API_KEY)
    index = get_or_create_index(pc)

    upsert_vectors(index, docs, vectors, args.batch)

    # ── Verify ────────────────────────────────────────────────────────────────
    stats = index.describe_index_stats()
    print(f"\nIndex stats after upsert:")
    print(f"  Total vectors : {stats['total_vector_count']}")
    print(f"  Dimensions    : {stats['dimension']}")
    print(f"\nDone. Index '{INDEX_NAME}' is ready to query.")


if __name__ == "__main__":
    main()