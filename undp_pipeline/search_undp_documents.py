import json
import numpy as np

from google.cloud import storage
from sentence_transformers import SentenceTransformer

BUCKET_NAME = "undp-project-documents-llm-2026"

EMBEDDINGS_PREFIX = "embeddings"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


def load_embeddings_from_gcs(bucket_name: str) -> list[dict]:
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=EMBEDDINGS_PREFIX)

    rows = []

    for blob in blobs:
        if not blob.name.endswith("_embeddings.jsonl"):
            continue

        print(f"Loading: gs://{bucket_name}/{blob.name}")
        content = blob.download_as_text(encoding="utf-8")

        for line in content.splitlines():
            if line.strip():
                rows.append(json.loads(line))

    return rows


def cosine_similarity(query_vector: np.ndarray, document_vectors: np.ndarray) -> np.ndarray:
    return document_vectors @ query_vector


def search(question: str, top_k: int = TOP_K):
    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print("\nLoading document embeddings from GCS...")
    rows = load_embeddings_from_gcs(BUCKET_NAME)

    if not rows:
        print("No embeddings found.")
        return

    print(f"Loaded {len(rows)} chunks.")

    print("\nEmbedding question...")
    query_vector = model.encode(
        question,
        normalize_embeddings=True,
    )

    document_vectors = np.array(
        [row["embedding"] for row in rows],
        dtype=np.float32,
    )

    scores = cosine_similarity(query_vector, document_vectors)

    sorted_indices = np.argsort(scores)[::-1]

    top_indices = []
    seen = set()

    for index in sorted_indices:
        row = rows[index]

        dedupe_key = (
            row.get("project_id"),
            row.get("file_name"),
            row.get("page_number"),
            row.get("text", "")[:300],
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        top_indices.append(index)

        if len(top_indices) >= top_k:
            break

    print("\nTop matching chunks:")
    print("=" * 80)

    for rank, index in enumerate(top_indices, start=1):
        row = rows[index]
        score = scores[index]

        print(f"\nRank: {rank}")
        print(f"Score: {score:.4f}")
        print(f"Country: {row.get('country')}")
        print(f"Year: {row.get('year')}")
        print(f"Project ID: {row.get('project_id')}")
        print(f"File: {row.get('file_name')}")
        print(f"Page: {row.get('page_number')}")
        print(f"Source: {row.get('source_gcs_path')}")
        print("-" * 80)
        print(row.get("text", "")[:1200])


def main():
    question = input("\nAsk a question about the UNDP documents: ").strip()

    if not question:
        print("No question entered.")
        return

    search(question)


if __name__ == "__main__":
    main()