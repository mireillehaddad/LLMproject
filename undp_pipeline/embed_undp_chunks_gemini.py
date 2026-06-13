import json
import time
from datetime import datetime, timezone

from google import genai
from google.cloud import storage

BUCKET_NAME = "undp-project-documents-llm-2026"
PROJECT_ID = "undp-project-documents"
LOCATION = "us-central1"

PROCESSED_PREFIX = "processed"
EMBEDDINGS_PREFIX = "embeddings"

MODEL_NAME = "gemini-embedding-001"
OUTPUT_DIMENSIONALITY = 768

YEARS = [2024, 2025, 2026]
COUNTRIES = ["Lebanon", "Egypt"]


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
    jsonl_text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)

    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        jsonl_text,
        content_type="application/jsonl",
    )

    print(f"Saved embeddings: gs://{BUCKET_NAME}/{blob_name}")


def get_embedding(client, text: str) -> list[float]:
    response = client.models.embed_content(
        model=MODEL_NAME,
        contents=text,
        config={
            "output_dimensionality": OUTPUT_DIMENSIONALITY,
        },
    )

    return response.embeddings[0].values


def process_chunks_file(bucket, blob, client):
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

    created_at = datetime.now(timezone.utc).isoformat()
    rows = []

    print(f"Creating Gemini embeddings for {len(chunks)} chunks...")

    for i, chunk in enumerate(chunks, start=1):
        text = chunk["text"]

        embedding = get_embedding(client, text)

        row = {
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "embedding": embedding,
            "source_gcs_path": chunk["source_gcs_path"],
            "year": chunk["year"],
            "country": chunk["country"],
            "project_id": chunk["project_id"],
            "file_name": chunk["file_name"],
            "page_number": chunk["page_number"],
            "embedding_model": MODEL_NAME,
            "embedding_dimension": OUTPUT_DIMENSIONALITY,
            "created_at": created_at,
        }

        rows.append(row)

        if i % 10 == 0:
            print(f"Embedded {i}/{len(chunks)} chunks")

        time.sleep(0.1)

    upload_jsonl_to_gcs(bucket, output_blob_name, rows)

    print(f"Total embeddings: {len(rows)}")
    return "embedded"


def main():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )

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

                status = process_chunks_file(bucket, blob, client)

                if status == "embedded":
                    total_embedded += 1
                elif status == "already_embedded":
                    total_skipped += 1
                elif status == "no_chunks":
                    total_no_chunks += 1

    print("\nGemini embedding pipeline complete.")
    print(f"Embedded files: {total_embedded}")
    print(f"Skipped already embedded files: {total_skipped}")
    print(f"Files with no chunks: {total_no_chunks}")


if __name__ == "__main__":
    main()