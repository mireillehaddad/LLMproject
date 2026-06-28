import json
import hashlib

from google.cloud import bigquery

from src.common.gcs_utils import download_text, list_blobs
from src.common.settings import settings


DATASET_ID = "undp_rag"
TABLE_ID = "rag_chunks"


def table_id() -> str:
    return f"{settings.project_id}.{DATASET_ID}.{TABLE_ID}"


def create_dataset_if_missing(client: bigquery.Client) -> None:
    dataset_ref = f"{settings.project_id}.{DATASET_ID}"

    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = settings.region

    client.create_dataset(dataset, exists_ok=True)

    print(f"Dataset ready: {dataset_ref}")


def create_table_if_missing(client: bigquery.Client) -> None:
    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("text", "STRING"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
        bigquery.SchemaField("source_pdf_blob", "STRING"),
        bigquery.SchemaField("page_number", "INT64"),
        bigquery.SchemaField("year", "STRING"),
        bigquery.SchemaField("country", "STRING"),
        bigquery.SchemaField("project_id", "STRING"),
        bigquery.SchemaField("embedding_blob", "STRING"),
    ]

    table = bigquery.Table(table_id(), schema=schema)
    client.create_table(table, exists_ok=True)

    print(f"Table ready: {table_id()}")


def get_metadata_value(record: dict, key: str) -> str | None:
    value = record.get(key)

    if value:
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
            return part.replace("year=", "").strip()

        if key == "country" and part.startswith("country="):
            return part.replace("country=", "").replace("_", " ").strip()

        if key == "project_id" and part.startswith("project_id="):
            return part.replace("project_id=", "").strip()

    return None


def make_row_id(blob: str, record: dict) -> str:
    raw_id = (
        f"{blob}|"
        f"{record.get('source_pdf_blob', '')}|"
        f"{record.get('page_number', '')}|"
        f"{record.get('text', '')[:200]}"
    )

    return hashlib.md5(raw_id.encode("utf-8")).hexdigest()


def build_rows() -> list[dict]:
    rows = []

    embedding_blobs = [
        blob
        for blob in list_blobs(settings.embeddings_prefix)
        if blob.lower().endswith(".jsonl")
    ]

    print(f"Found {len(embedding_blobs)} embedding files.")

    for blob in embedding_blobs:
        print(f"Reading: {blob}")

        text = download_text(blob)

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            embedding = record.get("embedding")

            if not embedding:
                continue

            rows.append(
                {
                    "id": make_row_id(blob, record),
                    "text": record.get("text", ""),
                    "embedding": [float(x) for x in embedding],
                    "source_pdf_blob": record.get("source_pdf_blob"),
                    "page_number": record.get("page_number"),
                    "year": get_metadata_value(record, "year"),
                    "country": get_metadata_value(record, "country"),
                    "project_id": get_metadata_value(record, "project_id"),
                    "embedding_blob": blob,
                }
            )

    return rows


def load_rows(client: bigquery.Client, rows: list[dict]) -> None:
    if not rows:
        print("No rows to load.")
        return

    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("text", "STRING"),
            bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            bigquery.SchemaField("source_pdf_blob", "STRING"),
            bigquery.SchemaField("page_number", "INT64"),
            bigquery.SchemaField("year", "STRING"),
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("project_id", "STRING"),
            bigquery.SchemaField("embedding_blob", "STRING"),
        ],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_json(
        rows,
        table_id(),
        job_config=job_config,
    )

    job.result()

    print(f"Loaded {len(rows)} rows into {table_id()}")


def run() -> None:
    client = bigquery.Client(project=settings.project_id)

    create_dataset_if_missing(client)
    create_table_if_missing(client)

    rows = build_rows()
    load_rows(client, rows)


if __name__ == "__main__":
    run()