
import hashlib
import json

from google.cloud import bigquery

from src.common.gcs_utils import download_text, list_blobs
from src.common.settings import settings


DATASET_ID = "undp_rag"
TABLE_ID = "rag_chunks_eval"
SEARCH_INDEX_NAME = "rag_chunks_eval_text_index"


def table_id() -> str:
    return f"{settings.project_id}.{DATASET_ID}.{TABLE_ID}"


def create_dataset_if_missing(client: bigquery.Client) -> None:
    dataset_ref = f"{settings.project_id}.{DATASET_ID}"

    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = settings.region

    client.create_dataset(dataset, exists_ok=True)

    print(f"Dataset ready: {dataset_ref}")


def evaluation_schema() -> list[bigquery.SchemaField]:
    return [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("chunk_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source_id", "STRING"),
        bigquery.SchemaField("text", "STRING"),
        bigquery.SchemaField(
            "embedding",
            "FLOAT64",
            mode="REPEATED",
        ),
        bigquery.SchemaField("source_pdf_blob", "STRING"),
        bigquery.SchemaField("file_name", "STRING"),
        bigquery.SchemaField("page_number", "INT64"),
        bigquery.SchemaField("chunk_index", "INT64"),
        bigquery.SchemaField("year", "INT64"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("project_id", "STRING"),
        bigquery.SchemaField("embedding_blob", "STRING"),
        bigquery.SchemaField("embedding_model", "STRING"),
        bigquery.SchemaField("embedding_dimension", "INT64"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
        bigquery.SchemaField("embedded_at", "TIMESTAMP"),
    ]


def create_table_if_missing(client: bigquery.Client) -> None:
    table = bigquery.Table(
        table_id(),
        schema=evaluation_schema(),
    )

    client.create_table(table, exists_ok=True)

    print(f"Evaluation table ready: {table_id()}")


def create_search_index(client: bigquery.Client) -> None:
    sql = f"""
    CREATE SEARCH INDEX IF NOT EXISTS {SEARCH_INDEX_NAME}
    ON `{table_id()}`(text)
    """

    client.query(sql).result()

    print("Evaluation search index ready.")


def get_metadata_value(
    record: dict,
    key: str,
) -> str | None:
    value = record.get(key)

    if value is not None and str(value).strip():
        return str(value).strip()

    source = (
        record.get("embedding_blob")
        or record.get("source_pdf_blob")
        or record.get("source_gcs_path")
        or record.get("gcs_path")
        or ""
    )

    for part in str(source).split("/"):
        if key == "year" and part.startswith("year="):
            return part.replace("year=", "", 1).strip()

        if key == "country" and part.startswith("country="):
            return (
                part.replace("country=", "", 1)
                .replace("_", " ")
                .strip()
            )

        if key == "project_id" and part.startswith("project_id="):
            return part.replace("project_id=", "", 1).strip()

    return None


def fallback_row_id(
    embedding_blob: str,
    record: dict,
) -> str:
    raw_id = (
        f"{embedding_blob}|"
        f"{record.get('source_pdf_blob', '')}|"
        f"{record.get('page_number', '')}|"
        f"{record.get('chunk_index', '')}|"
        f"{record.get('text', '')[:200]}"
    )

    return hashlib.sha256(
        raw_id.encode("utf-8")
    ).hexdigest()[:32]


def parse_optional_int(value) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_rows() -> list[dict]:
    rows: list[dict] = []

    embedding_blobs = [
        blob
        for blob in list_blobs(settings.eval_embeddings_prefix)
        if blob.lower().endswith(".jsonl")
    ]

    print(
        f"Found {len(embedding_blobs)} evaluation embedding files."
    )

    for blob in embedding_blobs:
        print(f"Reading: {blob}")

        text = download_text(blob)

        for line_number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(
                    f"Skipping invalid JSON in {blob}, "
                    f"line {line_number}: {exc}"
                )
                continue

            embedding = record.get("embedding")

            if not embedding:
                print(
                    f"Skipping record without embedding in "
                    f"{blob}, line {line_number}"
                )
                continue

            chunk_id = str(
                record.get("chunk_id") or ""
            ).strip()

            if not chunk_id:
                print(
                    f"Warning: missing chunk_id in "
                    f"{blob}, line {line_number}. "
                    "Using fallback ID."
                )

                chunk_id = fallback_row_id(
                    embedding_blob=blob,
                    record=record,
                )

            year = parse_optional_int(
                get_metadata_value(record, "year")
            )

            row = {
                # Use the stable evaluation chunk ID as the row ID.
                "id": chunk_id,
                "chunk_id": chunk_id,
                "source_id": record.get("source_id"),
                "text": record.get("text", ""),
                "embedding": [
                    float(value)
                    for value in embedding
                ],
                "source_pdf_blob": record.get(
                    "source_pdf_blob"
                ),
                "file_name": record.get("file_name"),
                "page_number": parse_optional_int(
                    record.get("page_number")
                ),
                "chunk_index": parse_optional_int(
                    record.get("chunk_index")
                ),
                "year": year,
                "country": get_metadata_value(
                    record,
                    "country",
                ),
                "project_id": get_metadata_value(
                    record,
                    "project_id",
                ),
                "embedding_blob": blob,
                "embedding_model": record.get(
                    "embedding_model"
                ),
                "embedding_dimension": parse_optional_int(
                    record.get("embedding_dimension")
                ),
                "created_at": record.get("created_at"),
                "embedded_at": record.get("embedded_at"),
            }

            rows.append(row)

    print(f"Prepared {len(rows)} evaluation rows.")

    return rows


def validate_unique_chunk_ids(rows: list[dict]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for row in rows:
        chunk_id = row["chunk_id"]

        if chunk_id in seen:
            duplicates.add(chunk_id)

        seen.add(chunk_id)

    if duplicates:
        sample = sorted(duplicates)[:10]

        raise ValueError(
            "Duplicate chunk IDs found before loading. "
            f"Examples: {sample}"
        )


def load_rows(
    client: bigquery.Client,
    rows: list[dict],
) -> None:
    if not rows:
        print("No evaluation rows to load.")
        return

    validate_unique_chunk_ids(rows)

    job_config = bigquery.LoadJobConfig(
        schema=evaluation_schema(),
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )

    job = client.load_table_from_json(
        rows,
        table_id(),
        job_config=job_config,
    )

    job.result()

    print(
        f"Loaded {len(rows)} evaluation rows "
        f"into {table_id()}"
    )


def run() -> None:
    print("Starting evaluation BigQuery load...")

    client = bigquery.Client(
        project=settings.project_id
    )

    create_dataset_if_missing(client)
    create_table_if_missing(client)

    rows = build_rows()
    load_rows(client, rows)

    create_search_index(client)

    print("Evaluation BigQuery load complete.")


if __name__ == "__main__":
    run()
