import csv
import io
import re
from datetime import datetime, timezone

import requests

from src.common.gcs_utils import blob_exists, upload_bytes, upload_text
from src.common.settings import settings


UNDP_PROJECT_LIST_URL = "https://api.open.undp.org/api/project_list/?year={year}"
UNDP_PROJECT_DETAILS_URL = "https://api.open.undp.org/api/projects/{project_id}.json"


def safe_filename(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^\w\-.]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text[:180]


def get_project_list(year: int) -> list[dict]:
    url = UNDP_PROJECT_LIST_URL.format(year=year)

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    data = response.json()
    projects_data = data.get("data", {})

    if isinstance(projects_data, dict):
        projects = projects_data.get("data", [])
    else:
        projects = projects_data

    if not isinstance(projects, list):
        return []

    return [
        project
        for project in projects
        if isinstance(project, dict)
    ]


def get_project_details(project_id: str) -> dict:
    url = UNDP_PROJECT_DETAILS_URL.format(project_id=project_id)

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    return response.json()


def extract_documents(project_details: dict) -> list[dict]:
    documents = project_details.get("documents", [])

    if isinstance(documents, dict):
        documents = documents.get("data", [])

    if not isinstance(documents, list):
        return []

    return documents


def get_pdf_url(document: dict) -> str | None:
    for key in ["url", "download_url", "document_url", "file_url"]:
        value = document.get(key)

        if value and str(value).lower().endswith(".pdf"):
            return str(value)

    value = document.get("url")

    if value and ".pdf" in str(value).lower():
        return str(value)

    return None


def download_pdf(url: str) -> bytes:
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    return response.content


def country_matches(project: dict) -> bool:
    project_country = str(
        project.get("country")
        or project.get("country_name")
        or project.get("countryname")
        or ""
    ).strip()

    return project_country in settings.countries


def run() -> None:
    uploaded_count = 0
    skipped_count = 0
    metadata_rows: list[dict] = []

    for year in settings.years:
        print(f"Fetching UNDP projects for year={year}")

        projects = get_project_list(year)

        for project in projects:
            
            if uploaded_count >= settings.max_new_pdfs:
                break

            if not country_matches(project):
                continue

            project_id = str(
                project.get("project_id")
                or project.get("id")
                or project.get("projectid")
                or ""
            ).strip()

            if not project_id:
                continue

            country = str(
                project.get("country")
                or project.get("country_name")
                or project.get("countryname")
                or "unknown"
            ).strip()

            try:
                details = get_project_details(project_id)
            except Exception as exc:
                print(f"Skipping project {project_id}: could not fetch details: {exc}")
                continue

            documents = extract_documents(details)

            for document in documents:
                if uploaded_count >= settings.max_new_pdfs:
                    break

                title = str(
                    document.get("title")
                    or document.get("name")
                    or document.get("document_name")
                    or "document"
                ).strip()

                if not title.lower().startswith("project document"):
                    continue

                pdf_url = get_pdf_url(document)

                if not pdf_url:
                    continue

                document_id = str(
                    document.get("id")
                    or document.get("document_id")
                    or safe_filename(title)
                )

                file_name = f"{document_id}_{safe_filename(title)}.pdf"

                blob_name = (
                    f"{settings.raw_prefix}/"
                    f"year={year}/"
                    f"country={safe_filename(country)}/"
                    f"project_id={project_id}/"
                    f"{file_name}"
                )

                if blob_exists(blob_name):
                    skipped_count += 1
                    print(
                        f"Skipped existing PDF: "
                        f"gs://{settings.bucket_name}/{blob_name}"
                    )
                    continue

                try:
                    print(f"Downloading PDF: {title}")

                    pdf_bytes = download_pdf(pdf_url)

                    upload_bytes(
                        blob_name,
                        pdf_bytes,
                        content_type="application/pdf",
                    )

                    uploaded_count += 1

                    print(f"Uploaded: gs://{settings.bucket_name}/{blob_name}")

                    metadata_rows.append(
                        {
                            "year": year,
                            "country": country,
                            "project_id": project_id,
                            "document_id": document_id,
                            "title": title,
                            "pdf_url": pdf_url,
                            "gcs_path": f"gs://{settings.bucket_name}/{blob_name}",
                            "uploaded_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                except Exception as exc:
                    print(f"Failed to process document {title}: {exc}")

    if metadata_rows:
        output = io.StringIO()

        writer = csv.DictWriter(
            output,
            fieldnames=metadata_rows[0].keys(),
        )

        writer.writeheader()
        writer.writerows(metadata_rows)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        metadata_blob = f"{settings.metadata_prefix}/ingest_metadata_{timestamp}.csv"

        upload_text(metadata_blob, output.getvalue())

        print(f"Uploaded metadata: gs://{settings.bucket_name}/{metadata_blob}")

    print()
    print("Ingestion complete.")
    print(f"Uploaded new PDFs: {uploaded_count}")
    print(f"Skipped existing PDFs: {skipped_count}")


if __name__ == "__main__":
    run()