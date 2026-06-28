import json
from collections import Counter

import requests

from src.common.settings import settings


UNDP_PROJECT_LIST_URL = "https://api.open.undp.org/api/project_list/?year={year}"
UNDP_PROJECT_DETAILS_URL = "https://api.open.undp.org/api/projects/{project_id}.json"


def get_pdf_url(document: dict) -> str | None:
    for key in ["url", "download_url", "document_url", "file_url"]:
        value = document.get(key)

        if value and ".pdf" in str(value).lower():
            return str(value)

    return None


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


def get_country(project: dict) -> str:
    return str(
        project.get("country")
        or project.get("country_name")
        or project.get("countryname")
        or "unknown"
    ).strip()


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


def get_document_category(document: dict) -> tuple[str, str]:
    category = str(document.get("category") or "unknown").strip()
    category_name = str(document.get("category_name") or "unknown").strip()

    return category, category_name


def print_sample_document(
    *,
    year: int,
    country: str,
    project_id: str,
    document: dict,
) -> None:
    print()
    print("=" * 80)
    print("SAMPLE DOCUMENT JSON")
    print("=" * 80)
    print(f"Year: {year}")
    print(f"Country: {country}")
    print(f"Project ID: {project_id}")
    print()
    print(json.dumps(document, ensure_ascii=False, indent=2))
    print("=" * 80)
    print()


def run() -> None:
    title_counter = Counter()
    category_counter = Counter()
    project_counter = Counter()
    key_counter = Counter()
    all_documents = []
    printed_sample_json = False

    for year in settings.years:
        print(f"Checking year={year}")

        projects = get_project_list(year)

        for project in projects:
            country = get_country(project)

            if country not in settings.countries:
                continue

            project_id = get_project_id(project)

            if not project_id:
                continue

            try:
                details = get_project_details(project_id)
            except Exception as exc:
                print(f"Skipping project {project_id}: {exc}")
                continue

            documents = extract_documents(details)

            for document in documents:
                title = get_document_title(document)
                url = get_pdf_url(document)

                if not url:
                    continue

                category, category_name = get_document_category(document)

                if not printed_sample_json:
                    print_sample_document(
                        year=year,
                        country=country,
                        project_id=project_id,
                        document=document,
                    )
                    printed_sample_json = True

                title_counter[title] += 1
                category_counter[(category, category_name)] += 1
                project_counter[project_id] += 1

                for key in document.keys():
                    key_counter[key] += 1

                all_documents.append(
                    {
                        "year": year,
                        "country": country,
                        "project_id": project_id,
                        "title": title,
                        "category": category,
                        "category_name": category_name,
                        "url": url,
                    }
                )

    print()
    print("Document categories:")
    for (category, category_name), count in category_counter.most_common():
        print(f"{count:>4} | {category:<8} | {category_name}")

    print()
    print("Document JSON keys found:")
    for key, count in key_counter.most_common():
        print(f"{count:>4} | {key}")

    print()
    print("Top document titles:")
    for title, count in title_counter.most_common(100):
        print(f"{count:>4} | {title}")

    print()
    print("Top projects by number of PDF documents:")
    for project_id, count in project_counter.most_common(25):
        print(f"{count:>4} | {project_id}")

    print()
    print("Sample PDF documents:")
    for item in all_documents[:100]:
        print(
            f"{item['year']} | "
            f"{item['country']} | "
            f"{item['project_id']} | "
            f"{item['category']} | "
            f"{item['category_name']} | "
            f"{item['title']}"
        )

    print()
    print("Inspection complete.")
    print(f"Total PDF documents found: {len(all_documents)}")
    print(f"Unique document titles: {len(title_counter)}")
    print(f"Unique document categories: {len(category_counter)}")
    print(f"Unique project IDs: {len(project_counter)}")


if __name__ == "__main__":
    run()