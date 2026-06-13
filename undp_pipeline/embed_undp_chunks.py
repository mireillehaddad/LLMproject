import json
from datetime import datetime, timezone

from google.cloud import storage
from sentence_transformers import SentenceTransformer

BUCKET_NAME = "undp-project-documents-llm-2026"

YEARS = [2024, 2025, 2026]
COUNTRIES = ["Lebanon", "Egypt"]

PROCESSED_PREFIX = "processed"
EMBEDDINGS_PREFIX = "embeddings"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def embedding_blob_name(processed_blob_name: str) -> str:
    return processed_blob_name.replace(
        PROCESSED_PREFIX,
        EMBEDDINGS_PREFIX,
        1,
    ).replace("_chunks.jsonl", "_embeddings.jsonl")


def blob_exists(bucket, blob_name: str) -> bool:
    return bucket.blob(blob_name).exists()


def read_jsonl_from_gcs(blob) -> list[dict]:
    content = blob.download_as_text(encoding="utf-8")
    return [json.loads(line) for line in content.splitlines() if line.strip()]


def upload_jsonl_to_gcs(bucket, blob_name: str, rows: list[dict]):
    jsonl_text = "\n".join(
        json.dumps(row, ensure_ascii=False) for row in rows
    )

    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        jsonl_text,
        content_type="application/jsonl",
    )

    print(f"Saved embeddings: gs://{BUCKET_NAME}/{blob_name}")


def process_chunks_file(bucket, blob, model):
    input_blob_name = blob.name
    output_blob_name = embedding_blob_name(input_blob_name)

    if blob_exists(bucket, output_blob_name):
        print(f"Already embedded, skipping: {output_blob_name}")
        return "already_embedded"

    print(f"\nReading chunks: gs://{BUCKET_NAME}/{input_blob_name}")

    chunks = read_jsonl_from_gcs(blob)

    if not chunks:
        print(f"No chunks found in: {input_blob_name}")
        return "no_chunks"

    texts = [chunk["text"] for chunk in chunks]

    print(f"Creating embeddings for {len(texts)} chunks...")

    vectors = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    created_at = datetime.now(timezone.utc).isoformat()

    rows = []

    for chunk, vector in zip(chunks, vectors):
        row = {
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "embedding": vector.tolist(),
            "source_gcs_path": chunk["source_gcs_path"],
            "year": chunk["year"],
            "country": chunk["country"],
            "project_id": chunk["project_id"],
            "file_name": chunk["file_name"],
            "page_number": chunk["page_number"],
            "embedding_model": MODEL_NAME,
            "created_at": created_at,
        }

        rows.append(row)

    upload_jsonl_to_gcs(bucket, output_blob_name, rows)

    print(f"Total embeddings: {len(rows)}")
    return "embedded"


def main():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    total_embedded = 0
    total_skipped = 0
    total_no_chunks = 0

    for year in YEARS:
        for country in COUNTRIES:
            prefix = f"{PROCESSED_PREFIX}/year={year}/country={country}/"

            print(f"\nSearching chunks under: gs://{BUCKET_NAME}/{prefix}")

            blobs = storage_client.list_blobs(BUCKET_NAME, prefix=prefix)

            for blob in blobs:
                if not blob.name.endswith("_chunks.jsonl"):
                    continue

                status = process_chunks_file(bucket, blob, model)

                if status == "embedded":
                    total_embedded += 1
                elif status == "already_embedded":
                    total_skipped += 1
                elif status == "no_chunks":
                    total_no_chunks += 1

    print("\nEmbedding pipeline complete.")
    print(f"Embedded files: {total_embedded}")
    print(f"Skipped already embedded files: {total_skipped}")
    print(f"Files with no chunks: {total_no_chunks}")


if __name__ == "__main__":
    main()