import json
import time
from datetime import datetime, timezone

from google import genai
from google.genai.types import EmbedContentConfig

from src.common.gcs_utils import blob_exists, download_text, list_blobs, upload_text
from src.common.settings import settings


OUTPUT_DIMENSIONALITY = 768
SLEEP_SECONDS = 0.1


def output_blob_name(chunk_blob_name: str) -> str:
    relative_path = chunk_blob_name.replace(
        f"{settings.processed_prefix}/",
        "",
        1,
    )

    return f"{settings.embeddings_prefix}/{relative_path}"


def parse_jsonl(text: str) -> list[dict]:
    return [
        json.loads(line)
        for line in text.splitlines()
        if line.strip()
    ]


def embed_text(client: genai.Client, text: str) -> list[float]:
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=OUTPUT_DIMENSIONALITY,
        ),
    )

    return response.embeddings[0].values


def process_chunk_file(
    client: genai.Client,
    chunk_blob_name: str,
) -> str:
    destination_blob = output_blob_name(chunk_blob_name)

    if blob_exists(destination_blob):
        print(f"Already embedded, skipping: {destination_blob}")
        return "already_embedded"

    chunk_text = download_text(chunk_blob_name)
    records = parse_jsonl(chunk_text)

    if not records:
        print(f"No chunks found in: {chunk_blob_name}")
        return "no_chunks"

    embedded_records = []
    embedded_at = datetime.now(timezone.utc).isoformat()

    print(f"Creating Gemini embeddings for {len(records)} chunks...")

    for index, record in enumerate(records, start=1):
        text = record["text"]

        embedding = embed_text(client, text)

        embedded_records.append(
            {
                **record,
                "embedding": embedding,
                "embedding_model": settings.embedding_model,
                "embedding_dimension": OUTPUT_DIMENSIONALITY,
                "embedded_at": embedded_at,
            }
        )

        if index % 10 == 0:
            print(f"Embedded {index}/{len(records)} chunks")

        time.sleep(SLEEP_SECONDS)

    output_text = "\n".join(
        json.dumps(record, ensure_ascii=False)
        for record in embedded_records
    )

    upload_text(destination_blob, output_text)

    print(f"Saved embeddings: gs://{settings.bucket_name}/{destination_blob}")

    return "embedded"


def run() -> None:
    print("Starting embedding job...")

    client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    print("Gemini client created")

    chunk_blobs = [
        blob
        for blob in list_blobs(settings.processed_prefix)
        if blob.lower().endswith(".jsonl")
    ]

    print(f"Found chunk files: {len(chunk_blobs)}")

    total_embedded = 0
    total_skipped = 0
    total_no_chunks = 0

    for chunk_blob in chunk_blobs:
        print(f"\nEmbedding: gs://{settings.bucket_name}/{chunk_blob}")

        try:
            status = process_chunk_file(
                client=client,
                chunk_blob_name=chunk_blob,
            )

            if status == "embedded":
                total_embedded += 1
            elif status == "already_embedded":
                total_skipped += 1
            elif status == "no_chunks":
                total_no_chunks += 1

        except Exception as exc:
            print(f"Failed to embed {chunk_blob}: {exc}")

    print()
    print("Embedding complete.")
    print(f"Embedded files: {total_embedded}")
    print(f"Skipped already embedded files: {total_skipped}")
    print(f"Files with no chunks: {total_no_chunks}")


if __name__ == "__main__":
    run()