import csv
import io
import re
from collections import Counter
from datetime import datetime, timezone

import requests

from src.common.gcs_utils import blob_exists, upload_bytes, upload_text
from src.common.settings import settings


UNDP_PROJECT_LIST_URL = "https://api.open.undp.org/api/project_list/?year={year}"
UNDP_PROJECT_DETAILS_URL = "https://api.open.undp.org/api/projects/{project_id}.json"

KEEP_CATEGORY = "A02"
KEEP_CATEGORY_NAME = "Project Document"


def safe_filename(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^\w\-.]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text[:180]


def get_project_list(year: int) -> list[dict]:
    response = requests.get(
        UNDP_PROJECT_LIST_URL.format(year=year),
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    projects_data = data.get("data", {})

    if isinstance(projects_data, dict):
        projects = projects_data.get("data", [])
    else:
        projects = projects_data

    return projects if isinstance(projects, list) else []


def get_project_details(project_id: str) -> dict:
    response = requests.get(
        UNDP_PROJECT_DETAILS_URL.format(project_id=project_id),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def extract_documents(project_details: dict) -> list[dict]:
    documents = project_details.get("documents", [])

    if isinstance(documents, dict):
        documents = documents.get("data", [])

    return documents if isinstance(documents, list) else []


def get_pdf_url(document: dict) -> str | None:
    for key in ["url", "download_url", "document_url", "file_url"]:
        value = document.get(key)

        if value and ".pdf" in str(value).lower():
            return str(value)

    return None


def download_pdf(url: str) -> bytes:
    response = requests.get(
        url,
        timeout=(15, 120),
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    return response.content


def get_project_country(project: dict) -> str:
    return str(
        project.get("country")
        or project.get("country_name")
        or project.get("countryname")
        or "unknown"
    ).strip()


def country_matches(project: dict) -> bool:
    return get_project_country(project) in settings.countries


def get_project_id(project: dict) -> str:
    return str(
        project.get("project_id")
        or project.get("id")
        or project.get("projectid")
        or ""
    ).strip()


def get_document_title(document: dict) -> str:
    return str(
        document.get("title")
        or document.get("name")
        or document.get("document_name")
        or "document"
    ).strip()


def is_project_document(document: dict) -> bool:
    category = str(document.get("category") or "").strip()
    category_name = str(document.get("category_name") or "").strip()

    return category == KEEP_CATEGORY or category_name == KEEP_CATEGORY_NAME


def is_probably_english(title: str, pdf_url: str) -> bool:
    text = f"{title} {pdf_url}".lower()

    non_english_markers = (
        "arabic",
        "arabe",
        "عربي",
        "_ar",
        "-ar",
        "/ar/",
        "french",
        "français",
        "francais",
        "_fr",
        "-fr",
        "/fr/",
        "spanish",
        "español",
        "espanol",
        "_es",
        "-es",
        "/es/",
    )

    return not any(marker in text for marker in non_english_markers)


def run() -> None:
    uploaded_count = 0
    skipped_count = 0
    skipped_category_count = 0
    skipped_language_count = 0
    metadata_rows: list[dict] = []

    country_counter = Counter()
    category_counter = Counter()

    for year in settings.years:
        print(f"Fetching UNDP projects for year={year}")

        projects = get_project_list(year)

        for project in projects:
            country = get_project_country(project)
            country_counter[country] += 1

            if uploaded_count >= settings.max_new_pdfs:
                break

            if not country_matches(project):
                continue

            project_id = get_project_id(project)

            if not project_id:
                continue

            try:
                details = get_project_details(project_id)
            except Exception as exc:
                print(f"Skipping project {project_id}: could not fetch details: {exc}")
                continue

            documents = extract_documents(details)

            for document in documents:
                if uploaded_count >= settings.max_new_pdfs:
                    break

                title = get_document_title(document)

                category = str(document.get("category") or "unknown").strip()
                category_name = str(document.get("category_name") or "unknown").strip()
                category_counter[(category, category_name)] += 1

                if not is_project_document(document):
                    skipped_category_count += 1
                    continue

                pdf_url = get_pdf_url(document)

                if not pdf_url:
                    continue

                if not is_probably_english(title, pdf_url):
                    skipped_language_count += 1
                    print(f"Skipping non-English document: {title}")
                    continue

                document_id = str(
                    document.get("id")
                    or document.get("document_id")
                    or safe_filename(title)
                ).strip()

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
                    print(f"Skipped existing PDF: gs://{settings.bucket_name}/{blob_name}")
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
                            "category": category,
                            "category_name": category_name,
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
    print("Document categories seen:")
    for (category, category_name), count in category_counter.most_common():
        print(f"{count:>4} | {category} | {category_name}")

    print()
    print("Top countries found:")
    for country, count in country_counter.most_common(50):
        print(f"{country}: {count}")

    print()
    print("Ingestion complete.")
    print(f"Uploaded new PDFs: {uploaded_count}")
    print(f"Skipped existing PDFs: {skipped_count}")
    print(f"Skipped non-project-document category: {skipped_category_count}")
    print(f"Skipped probable non-English documents: {skipped_language_count}")


if __name__ == "__main__":
    run()