import io
import json
from datetime import datetime, timezone

from pypdf import PdfReader

from src.common.gcs_utils import (
    blob_exists,
    download_bytes,
    list_blobs,
    upload_text,
)
from src.common.settings import settings


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def output_blob_name(pdf_blob_name: str) -> str:
    relative_path = pdf_blob_name.replace(
        f"{settings.raw_prefix}/",
        "",
        1,
    )

    return f"{settings.processed_prefix}/{relative_path}.jsonl"


def process_pdf(pdf_blob_name: str) -> str:
    destination_blob = output_blob_name(pdf_blob_name)

    if blob_exists(destination_blob):
        print(f"Already chunked, skipping: {destination_blob}")
        return "already_chunked"

    pdf_bytes = download_bytes(pdf_blob_name)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    records: list[dict] = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())

        if not text:
            continue

        chunks = chunk_text(text)

        for chunk_index, chunk in enumerate(chunks, start=1):
            records.append(
                {
                    "source_pdf_blob": pdf_blob_name,
                    "page_number": page_index,
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    if not records:
        print(f"No text chunks found in: {pdf_blob_name}")
        return "no_chunks"

    output_text = "\n".join(
        json.dumps(record, ensure_ascii=False)
        for record in records
    )

    upload_text(destination_blob, output_text)

    print(f"Saved chunks: gs://{settings.bucket_name}/{destination_blob}")

    return "chunked"


def run() -> None:
    pdf_blobs = [
        blob
        for blob in list_blobs(settings.raw_prefix)
        if blob.lower().endswith(".pdf")
    ]

    print(f"Found PDFs: {len(pdf_blobs)}")

    total_chunked = 0
    total_skipped = 0
    total_no_chunks = 0

    for pdf_blob in pdf_blobs:
        print(f"\nChunking: gs://{settings.bucket_name}/{pdf_blob}")

        try:
            status = process_pdf(pdf_blob)

            if status == "chunked":
                total_chunked += 1
            elif status == "already_chunked":
                total_skipped += 1
            elif status == "no_chunks":
                total_no_chunks += 1

        except Exception as exc:
            print(f"Failed to chunk {pdf_blob}: {exc}")

    print()
    print("Chunking complete.")
    print(f"PDFs newly chunked: {total_chunked}")
    print(f"PDFs skipped because already chunked: {total_skipped}")
    print(f"PDFs with no chunks: {total_no_chunks}")


if __name__ == "__main__":
    run()