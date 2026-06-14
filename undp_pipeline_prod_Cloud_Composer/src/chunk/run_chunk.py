import io
import json
from datetime import datetime, timezone

from pypdf import PdfReader

from src.common.gcs_utils import (
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


def process_pdf(pdf_blob_name: str) -> int:
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
                    "created_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )

    output_text = "\n".join(
        json.dumps(
            record,
            ensure_ascii=False,
        )
        for record in records
    )

    destination_blob = output_blob_name(pdf_blob_name)

    upload_text(
        destination_blob,
        output_text,
    )

    return len(records)


def run() -> None:
    pdf_blobs = [
        blob
        for blob in list_blobs(settings.raw_prefix)
        if blob.lower().endswith(".pdf")
    ]

    print(f"Found PDFs: {len(pdf_blobs)}")

    total_chunks = 0

    for pdf_blob in pdf_blobs:
        print(
            f"Chunking: "
            f"gs://{settings.bucket_name}/{pdf_blob}"
        )

        try:
            chunk_count = process_pdf(pdf_blob)

            total_chunks += chunk_count

            print(f"Created chunks: {chunk_count}")

        except Exception as exc:
            print(
                f"Failed to chunk "
                f"{pdf_blob}: {exc}"
            )

    print()
    print("Chunking complete.")
    print(f"Total PDFs processed: {len(pdf_blobs)}")
    print(f"Total chunks created: {total_chunks}")


if __name__ == "__main__":
    run()