import io
import json
import re
from datetime import datetime, timezone

from google.cloud import storage
from pypdf import PdfReader

BUCKET_NAME = "undp-project-documents-llm-2026"

YEARS = [2024, 2025, 2026]
COUNTRIES = ["Lebanon", "Egypt"]

RAW_PREFIX = "raw"
PROCESSED_PREFIX = "processed"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> list[dict]:
    reader = PdfReader(io.BytesIO(pdf_bytes))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = clean_text(text)

        if text:
            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                }
            )

    return pages


def split_text_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

        if start < 0:
            start = 0

        if start >= text_length:
            break

    return chunks


def parse_metadata_from_blob_name(blob_name: str) -> dict:
    parts = blob_name.split("/")

    year = None
    country = None
    project_id = None
    file_name = parts[-1]

    for part in parts:
        if part.startswith("year="):
            year = part.replace("year=", "")

        if part.startswith("country="):
            country = part.replace("country=", "")

        if part.startswith("project_id="):
            project_id = part.replace("project_id=", "")

    return {
        "year": year,
        "country": country,
        "project_id": project_id,
        "file_name": file_name,
    }


def processed_blob_name(raw_blob_name: str) -> str:
    metadata = parse_metadata_from_blob_name(raw_blob_name)

    year = metadata["year"]
    country = metadata["country"]
    project_id = metadata["project_id"]

    pdf_file_name = metadata["file_name"]
    base_name = pdf_file_name.replace(".pdf", "")

    return (
        f"{PROCESSED_PREFIX}/"
        f"year={year}/"
        f"country={country}/"
        f"project_id={project_id}/"
        f"{base_name}_chunks.jsonl"
    )


def blob_exists(bucket, blob_name: str) -> bool:
    return bucket.blob(blob_name).exists()


def process_pdf_blob(bucket, blob):
    raw_blob_name = blob.name
    output_blob_name = processed_blob_name(raw_blob_name)

    if blob_exists(bucket, output_blob_name):
        print(f"Already processed, skipping: {output_blob_name}")
        return "already_processed"

    print(f"\nReading PDF: gs://{BUCKET_NAME}/{raw_blob_name}")

    pdf_bytes = blob.download_as_bytes()
    pages = extract_text_from_pdf(pdf_bytes)

    if not pages:
        print(f"No text extracted from: {raw_blob_name}")
        return "no_text"

    metadata = parse_metadata_from_blob_name(raw_blob_name)

    records = []
    chunk_id = 0
    ingested_at = datetime.now(timezone.utc).isoformat()

    for page in pages:
        page_number = page["page_number"]
        page_text = page["text"]

        chunks = split_text_into_chunks(
            text=page_text,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP,
        )

        for chunk_text in chunks:
            chunk_id += 1

            record = {
                "chunk_id": chunk_id,
                "text": chunk_text,
                "source_gcs_path": f"gs://{BUCKET_NAME}/{raw_blob_name}",
                "year": metadata["year"],
                "country": metadata["country"],
                "project_id": metadata["project_id"],
                "file_name": metadata["file_name"],
                "page_number": page_number,
                "created_at": ingested_at,
            }

            records.append(record)

    jsonl_text = "\n".join(json.dumps(row, ensure_ascii=False) for row in records)

    output_blob = bucket.blob(output_blob_name)
    output_blob.upload_from_string(
        jsonl_text,
        content_type="application/jsonl",
    )

    print(f"Saved chunks: gs://{BUCKET_NAME}/{output_blob_name}")
    print(f"Total chunks: {len(records)}")

    return "processed"


def main():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    total_processed = 0
    total_skipped = 0
    total_no_text = 0

    for year in YEARS:
        for country in COUNTRIES:
            prefix = f"{RAW_PREFIX}/year={year}/country={country}/"

            print(f"\nSearching PDFs under: gs://{BUCKET_NAME}/{prefix}")

            blobs = storage_client.list_blobs(BUCKET_NAME, prefix=prefix)

            for blob in blobs:
                if not blob.name.lower().endswith(".pdf"):
                    continue

                status = process_pdf_blob(bucket, blob)

                if status == "processed":
                    total_processed += 1
                elif status == "already_processed":
                    total_skipped += 1
                elif status == "no_text":
                    total_no_text += 1

    print("\nChunking complete.")
    print(f"Processed PDFs: {total_processed}")
    print(f"Skipped already processed PDFs: {total_skipped}")
    print(f"PDFs with no extracted text: {total_no_text}")


if __name__ == "__main__":
    main()