import csv
import io
import re
import time
from datetime import datetime, timezone

import requests
from google.cloud import storage

BUCKET_NAME = "undp-project-documents-llm-2026"

YEARS = [2024, 2025, 2026]
MAX_NEW_PDFS = 50
COUNTRY_FILTERS = {"Lebanon", "Egypt"}


def safe_filename(text: str) -> str:
    text = str(text).strip()
    text = re.sub(r"[^\w\-. ]+", "_", text)
    text = re.sub(r"\s+", "_", text)
    return text[:180]


def is_allowed_document_title(title: str) -> bool:
    return title.lower().startswith("project document")


def blob_exists(bucket, blob_name: str) -> bool:
    return bucket.blob(blob_name).exists()


def upload_pdf_to_gcs(bucket, blob_name: str, pdf_bytes: bytes):
    blob = bucket.blob(blob_name)
    blob.upload_from_string(pdf_bytes, content_type="application/pdf")
    print(f"Uploaded: gs://{BUCKET_NAME}/{blob_name}")


def upload_metadata_to_gcs(bucket, rows: list[dict], year: int):
    if not rows:
        print(f"No metadata to upload for {year}.")
        return

    output = io.StringIO()

    fieldnames = [
        "ingested_at",
        "year",
        "country",
        "project_id",
        "project_title",
        "document_id",
        "document_title",
        "document_url",
        "gcs_path",
        "status",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    metadata_name = f"metadata/year={year}/metadata_{timestamp}.csv"

    blob = bucket.blob(metadata_name)
    blob.upload_from_string(output.getvalue(), content_type="text/csv")

    print(f"Uploaded metadata: gs://{BUCKET_NAME}/{metadata_name}")


def get_project_list(year: int):
    url = "https://api.open.undp.org/api/project_list/"
    response = requests.get(url, params={"year": year}, timeout=60)
    response.raise_for_status()
    return response.json()["data"]["data"]


def get_project_details(project_id: str):
    url = f"https://api.open.undp.org/api/projects/{project_id}.json"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def download_pdf(url: str) -> bytes:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.content


def process_year(bucket, year: int, ingested_at: str) -> tuple[int, int]:
    projects = get_project_list(year)
    print(f"\nFound {len(projects)} projects for {year}")

    uploaded_count = 0
    skipped_existing_count = 0
    metadata_rows = []

    for project in projects:
        country = project.get("country", "")

        if country not in COUNTRY_FILTERS:
            continue

        project_id = project["project_id"]
        project_title = project.get("title", "")

        print(f"\nChecking project {project_id}: {project_title} ({country})")

        details = get_project_details(project_id)
        documents = details.get("documents", [])

        for doc in documents:
            category_name = doc.get("category_name", "")
            fmt = doc.get("format", "")
            document_url = doc.get("document_url")
            doc_title = doc.get("title", "project_document")
            doc_id = doc.get("id", "no_id")

            if not document_url:
                continue

            if fmt != "application/pdf":
                continue

            if category_name != "Project Document":
                continue

            if not is_allowed_document_title(doc_title):
                print(f"Skipping title: {doc_title}")
                continue

            blob_name = (
                f"raw/year={year}/"
                f"country={safe_filename(country)}/"
                f"project_id={project_id}/"
                f"{doc_id}_{safe_filename(doc_title)}.pdf"
            )

            gcs_path = f"gs://{BUCKET_NAME}/{blob_name}"

            row = {
                "ingested_at": ingested_at,
                "year": year,
                "country": country,
                "project_id": project_id,
                "project_title": project_title,
                "document_id": doc_id,
                "document_title": doc_title,
                "document_url": document_url,
                "gcs_path": gcs_path,
                "status": "",
            }

            if blob_exists(bucket, blob_name):
                print(f"Already exists, skipping download: {doc_title}")
                skipped_existing_count += 1
                row["status"] = "already_exists"
                metadata_rows.append(row)
                continue

            print(f"Downloading PDF: {doc_title}")
            pdf_bytes = download_pdf(document_url)

            upload_pdf_to_gcs(bucket, blob_name, pdf_bytes)

            uploaded_count += 1
            row["status"] = "uploaded"
            metadata_rows.append(row)

            if uploaded_count >= MAX_NEW_PDFS:
                print(f"\nReached MAX_NEW_PDFS={MAX_NEW_PDFS} for {year}.")
                upload_metadata_to_gcs(bucket, metadata_rows, year)
                return uploaded_count, skipped_existing_count

            time.sleep(0.5)

    upload_metadata_to_gcs(bucket, metadata_rows, year)
    return uploaded_count, skipped_existing_count


def main():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    ingested_at = datetime.now(timezone.utc).isoformat()

    total_uploaded = 0
    total_skipped_existing = 0

    for year in YEARS:
        uploaded, skipped_existing = process_year(bucket, year, ingested_at)
        total_uploaded += uploaded
        total_skipped_existing += skipped_existing

    print("\nPipeline complete.")
    print(f"Uploaded new PDFs: {total_uploaded}")
    print(f"Skipped existing PDFs: {total_skipped_existing}")


if __name__ == "__main__":
    main()