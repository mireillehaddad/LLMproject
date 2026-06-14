# Step 1 — Enable Required Google Cloud Services

Before creating Cloud Run Jobs, Cloud Composer, or deploying the chatbot, configure your Google Cloud project and enable all required services.

---

## 1. Set the Google Cloud Project

Open **PowerShell** and run:

```powershell
gcloud config set project undp-project-documents
```

Verify the active project:

```powershell
gcloud config get-value project
```

Expected output:

```text
undp-project-documents
```

---

## 2. Enable Required APIs

Run:

```powershell
gcloud services enable ^
run.googleapis.com ^
cloudbuild.googleapis.com ^
artifactregistry.googleapis.com ^
composer.googleapis.com ^
storage.googleapis.com ^
aiplatform.googleapis.com
```

If PowerShell does not accept the `^` line continuation character, run the command as a single line:

```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com composer.googleapis.com storage.googleapis.com aiplatform.googleapis.com
```

---

## 3. Verify Cloud Composer Is Enabled

Run:

```powershell
gcloud services list --enabled | findstr composer
```

Expected output:

```text
composer.googleapis.com
```

---

## Services Used in the UNDP Production Architecture

| Service           | Purpose                                          |
| ----------------- | ------------------------------------------------ |
| Cloud Run         | Executes ingestion, chunking, and embedding jobs |
| Cloud Build       | CI/CD deployment pipeline                        |
| Artifact Registry | Stores Docker container images                   |
| Cloud Composer    | Orchestrates workflows using Airflow DAGs        |
| Cloud Storage     | Stores PDFs, chunks, metadata, and embeddings    |
| Vertex AI         | Generates embeddings and Gemini responses        |

---

## Architecture Goal

```text
UNDP API
   ↓
Cloud Run Job: Ingest PDFs
   ↓
GCS raw/
   ↓
Cloud Run Job: Chunk PDFs
   ↓
GCS processed/
   ↓
Cloud Run Job: Create Embeddings
   ↓
GCS embeddings/
   ↓
Cloud Run / Streamlit Chatbot
```

Once all services are enabled successfully, continue to 

**Step 2 — Create the GCS Bucket and Folder Structure**.




# Step 2 — Create the GCS Bucket and Folder Structure
# Step 2 — Create the GCS Bucket and Folder Structure

The UNDP pipeline stores PDFs, processed chunks, embeddings, and metadata in a Google Cloud Storage (GCS) bucket.

---

## 1. Create the Storage Bucket

Create the bucket in the same region as the rest of the project:

```powershell
gcloud storage buckets create gs://undp-project-documents-llm-prod `
    --location=northamerica-northeast1 `
    --uniform-bucket-level-access
```

Verify that the bucket exists:

```powershell
gcloud storage buckets list
```

Expected output should contain:

```text
gs://undp-project-documents-llm-prod
```

---

## 2. Create Folder Structure

Google Cloud Storage does not have real folders, but creating placeholder objects helps organize the project.

Create the following structure:

```text
raw/
processed/
embeddings/
metadata/
logs/
```

Run:

```powershell

"" | gcloud storage cp - gs://undp-project-documents-llm-prod/raw/.keep

"" | gcloud storage cp - gs://undp-project-documents-llm-prod/processed/.keep

"" | gcloud storage cp - gs://undp-project-documents-llm-prod/embeddings/.keep

"" | gcloud storage cp - gs://undp-project-documents-llm-prod/metadata/.keep

"" | gcloud storage cp - gs://undp-project-documents-llm-prod/logs/.keep
```

---

## 3. Verify Folder Structure

List bucket contents:

```powershell
gcloud storage ls gs://undp-project-documents-llm-prod
```

Expected:

```text
gs://undp-project-documents-llm-prod/raw/
gs://undp-project-documents-llm-prod/processed/
gs://undp-project-documents-llm-prod/embeddings/
gs://undp-project-documents-llm-prod/metadata/
gs://undp-project-documents-llm-prod/logs/
```

---

## 4. Purpose of Each Folder

| Folder      | Purpose                                    |
| ----------- | ------------------------------------------ |
| raw/        | Original PDFs downloaded from the UNDP API |
| processed/  | Chunked text extracted from PDFs           |
| embeddings/ | Vector embeddings generated from chunks    |
| metadata/   | CSV and JSON metadata files                |
| logs/       | Pipeline execution logs                    |

---

## Expected Production Data Flow

```text
UNDP API
   ↓
raw/
   ↓
processed/
   ↓
embeddings/
   ↓
Gemini Retrieval
   ↓
Chatbot Response
```

After the bucket and folder structure are created, continue to

 **Step 3 — Create the Python Project and Virtual Environment**.

# Step 3 — Create the Python Project and Virtual Environment

This step creates the local Python project folder, initializes the project with `uv`, creates a virtual environment, and installs the dependencies required for the UNDP production pipeline.

---

## 1. Go to Your Project Folder

Open PowerShell and navigate to your project directory:

```powershell
cd C:\Users\mirei\OneDrive\Desktop\LLMproject
```

---

## 2. Create the Pipeline Folder

Create a folder for the production pipeline:

```powershell
mkdir undp_pipeline_prod
cd undp_pipeline_prod
```

---

## 3. Initialize the Python Project

Create a new `uv` project:

```powershell
uv init
```

This creates a `pyproject.toml` file that will manage the project's dependencies.

---

## 4. Create the Virtual Environment

Run:

```powershell
uv venv
```

---

## 5. Activate the Virtual Environment

Run:

```powershell
.venv\Scripts\Activate.ps1
```

After activation, your terminal should show something similar to:

```text
(.venv) PS C:\Users\mirei\OneDrive\Desktop\LLMproject\undp_pipeline_prod>
```

---

## 6. Add Required Dependencies

Install and register the dependencies in `pyproject.toml`:

```powershell
uv add requests google-cloud-storage google-cloud-aiplatform google-genai python-dotenv pypdf numpy pandas streamlit
```

---

## 7. Create the Lock File

Generate the dependency lock file:

```powershell
uv lock
```

This creates:

```text
uv.lock
```

which guarantees reproducible environments across local development, Cloud Build, Cloud Run Jobs, and Cloud Composer.

---

## 8. Verify Installation

Run:

```powershell
python --version
uv --version
```

Verify the project files:

```powershell
dir
```

Expected files:

```text
.venv/
pyproject.toml
uv.lock
README.md
```

---

## Project Structure So Far

```text
Project Structure So Far
undp_pipeline_prod/
│
├── .venv/
├── .python-version
├── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

You are now ready for **Step 4 — Create the Project File Structure**.

# Step 4 — Create the Project File Structure

This step creates a clean production-ready folder structure for the UNDP pipeline.

The structure will support:

* Cloud Run Jobs for ingestion, chunking, and embeddings
* Cloud Composer DAGs for orchestration
* Streamlit chatbot application
* Docker deployment
* Tests and reusable source code

---

## 1. Make Sure You Are in the Project Folder

```powershell
cd C:\Users\mirei\OneDrive\Desktop\LLMproject\undp_pipeline_prod
```

---

## 2. Create the Main Folders

Run:

```powershell
mkdir src
mkdir src\ingest
mkdir src\chunk
mkdir src\embed
mkdir src\chatbot
mkdir src\common
mkdir dags
mkdir docker
mkdir tests
mkdir scripts
mkdir config
```

---

## 3. Create Python Package Files

Run:

```powershell
New-Item src\__init__.py -ItemType File
New-Item src\ingest\__init__.py -ItemType File
New-Item src\chunk\__init__.py -ItemType File
New-Item src\embed\__init__.py -ItemType File
New-Item src\chatbot\__init__.py -ItemType File
New-Item src\common\__init__.py -ItemType File
```

---

## 4. Create Starter Python Files

Run:

```powershell
New-Item src\ingest\run_ingest.py -ItemType File
New-Item src\chunk\run_chunk.py -ItemType File
New-Item src\embed\run_embed.py -ItemType File
New-Item src\chatbot\app.py -ItemType File
New-Item src\common\settings.py -ItemType File
New-Item src\common\gcs_utils.py -ItemType File
```

---

## 5. Create Deployment and Orchestration Files

Run:

```powershell
New-Item dags\undp_pipeline_dag.py -ItemType File
New-Item docker\Dockerfile.ingest -ItemType File
New-Item docker\Dockerfile.chunk -ItemType File
New-Item docker\Dockerfile.embed -ItemType File
New-Item docker\Dockerfile.chatbot -ItemType File
New-Item cloudbuild.yaml -ItemType File
New-Item .gitignore -ItemType File
New-Item .env.example -ItemType File
```

---

## 6. Verify the Structure

Run:

```powershell
tree /F
```

Expected structure:

```text
undp_pipeline_prod/
│   .env.example
│   .gitignore
│   .python-version
│   cloudbuild.yaml
│   main.py
│   pyproject.toml
│   README.md
│   uv.lock
│
├── config/
│
├── dags/
│       undp_pipeline_dag.py
│
├── docker/
│       Dockerfile.chatbot
│       Dockerfile.chunk
│       Dockerfile.embed
│       Dockerfile.ingest
│
├── scripts/
│
├── src/
│   │   __init__.py
│   │
│   ├── chatbot/
│   │       __init__.py
│   │       app.py
│   │
│   ├── chunk/
│   │       __init__.py
│   │       run_chunk.py
│   │
│   ├── common/
│   │       __init__.py
│   │       gcs_utils.py
│   │       settings.py
│   │
│   ├── embed/
│   │       __init__.py
│   │       run_embed.py
│   │
│   └── ingest/
│           __init__.py
│           run_ingest.py
│
└── tests/
```

---

## Purpose of Each Folder

| Folder         | Purpose                                                  |
| -------------- | -------------------------------------------------------- |
| `src/ingest/`  | Code for downloading UNDP PDFs and uploading them to GCS |
| `src/chunk/`   | Code for extracting text from PDFs and creating chunks   |
| `src/embed/`   | Code for creating embeddings and saving them             |
| `src/chatbot/` | Streamlit chatbot application                            |
| `src/common/`  | Shared configuration and GCS helper functions            |
| `dags/`        | Cloud Composer / Airflow DAG files                       |
| `docker/`      | Dockerfiles for Cloud Run Jobs and chatbot deployment    |
| `tests/`       | Unit tests                                               |
| `scripts/`     | Local helper scripts                                     |
| `config/`      | Configuration files                                      |

---

After creating this structure, continue to **Step 5 — Add Project Configuration Files**.


Step 5 — Add Project Configuration Files

This step adds the basic configuration files used by the local pipeline, Cloud Run Jobs, Cloud Build, and Cloud Composer.

1. Make Sure You Are in the Project Folder
cd C:\Users\mirei\OneDrive\Desktop\LLMproject\undp_pipeline_prod
2. Add .env.example

Open .env.example and add:

PROJECT_ID=undp-project-documents
REGION=northamerica-northeast1
BUCKET_NAME=undp-project-documents-llm-prod

YEARS=2024,2025,2026
COUNTRIES=Lebanon,Egypt
MAX_NEW_PDFS=50

RAW_PREFIX=raw
PROCESSED_PREFIX=processed
EMBEDDINGS_PREFIX=embeddings
METADATA_PREFIX=metadata

EMBEDDING_MODEL=gemini-embedding-001
GENERATION_MODEL=gemini-2.5-flash
3. Add .gitignore

Open .gitignore and add:

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd

# Virtual environment
.venv/
venv/

# Environment files
.env

# Local data
data/
*.pdf
*.jsonl
*.csv

# Streamlit
.streamlit/

# OS / editor
.DS_Store
Thumbs.db
.vscode/
.idea/
4. Add src/common/settings.py

Open src\common\settings.py and add:

import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_id: str = os.getenv("PROJECT_ID", "undp-project-documents")
    region: str = os.getenv("REGION", "northamerica-northeast1")
    bucket_name: str = os.getenv("BUCKET_NAME", "undp-project-documents-llm-prod")

    years: tuple[int, ...] = tuple(
        int(year.strip())
        for year in os.getenv("YEARS", "2024,2025,2026").split(",")
        if year.strip()
    )

    countries: tuple[str, ...] = tuple(
        country.strip()
        for country in os.getenv("COUNTRIES", "Lebanon,Egypt").split(",")
        if country.strip()
    )

    max_new_pdfs: int = int(os.getenv("MAX_NEW_PDFS", "50"))

    raw_prefix: str = os.getenv("RAW_PREFIX", "raw")
    processed_prefix: str = os.getenv("PROCESSED_PREFIX", "processed")
    embeddings_prefix: str = os.getenv("EMBEDDINGS_PREFIX", "embeddings")
    metadata_prefix: str = os.getenv("METADATA_PREFIX", "metadata")

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    generation_model: str = os.getenv("GENERATION_MODEL", "gemini-2.5-flash")


settings = Settings()
5. Add src/common/gcs_utils.py

Open src\common\gcs_utils.py and add:

from google.cloud import storage

from src.common.settings import settings


def get_bucket():
    client = storage.Client(project=settings.project_id)
    return client.bucket(settings.bucket_name)


def blob_exists(blob_name: str) -> bool:
    bucket = get_bucket()
    return bucket.blob(blob_name).exists()


def upload_bytes(blob_name: str, data: bytes, content_type: str | None = None) -> None:
    bucket = get_bucket()
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data, content_type=content_type)


def upload_text(blob_name: str, text: str) -> None:
    upload_bytes(blob_name, text.encode("utf-8"), content_type="text/plain")


def download_bytes(blob_name: str) -> bytes:
    bucket = get_bucket()
    return bucket.blob(blob_name).download_as_bytes()


def download_text(blob_name: str) -> str:
    return download_bytes(blob_name).decode("utf-8")


def list_blobs(prefix: str) -> list[str]:
    bucket = get_bucket()
    return [blob.name for blob in bucket.list_blobs(prefix=prefix)]
6. Verify Configuration Files

Run:

python -c "from src.common.settings import settings; print(settings)"

Expected output should include:

project_id='undp-project-documents'
region='northamerica-northeast1'
bucket_name='undp-project-documents-llm-prod'

# Step 6 — Add the UNDP Ingestion Job

This step adds the ingestion script that downloads UNDP project PDFs and uploads them to Google Cloud Storage under the `raw/` folder.

---

## 1. Open the Ingestion File

Open:

```text
src\ingest\run_ingest.py
```

---

## 2. Add the Ingestion Code

Paste this code:

```python
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
```

---

## 3. Run the Ingestion Job Locally

From the project root, run:

```powershell
python -m src.ingest.run_ingest
```

---

## 4. Expected Output

You should see messages similar to:

```text
Fetching UNDP projects for year=2024
Fetching UNDP projects for year=2025
Fetching UNDP projects for year=2026
Downloading PDF: Project Document
Uploaded: gs://undp-project-documents-llm-prod/raw/year=2026/country=Lebanon/project_id=.../document.pdf
Uploaded metadata: gs://undp-project-documents-llm-prod/metadata/ingest_metadata_YYYYMMDD_HHMMSS.csv

Ingestion complete.
Uploaded new PDFs: 12
Skipped existing PDFs: 0
```

---

## 5. Verify Files in GCS

Run:

```powershell
gcloud storage ls gs://undp-project-documents-llm-prod/raw/ --recursive
```

You should see uploaded PDF files under paths like:

```text
gs://undp-project-documents-llm-prod/raw/year=2026/country=Lebanon/project_id=01003798/3406425_Project_Document_ProDoc_.pdf
```

Also verify metadata:

```powershell
gcloud storage ls gs://undp-project-documents-llm-prod/metadata/
```

---

## What This Job Does

| Step | Description                                     |
| ---- | ----------------------------------------------- |
| 1    | Reads years and countries from project settings |
| 2    | Calls the UNDP project list API                 |
| 3    | Handles the nested UNDP API response            |
| 4    | Filters projects by country                     |
| 5    | Gets project details                            |
| 6    | Finds project documents                         |
| 7    | Downloads PDF files                             |
| 8    | Uploads PDFs to GCS `raw/`                      |
| 9    | Saves ingestion metadata to GCS `metadata/`     |

You are ready for **Step 7 — Add the PDF Chunking Job**.

# Step 7 — Add the PDF Chunking Job

This step creates the PDF chunking job that reads PDF files from Google Cloud Storage, extracts text, splits it into overlapping chunks, and stores the chunked output in the `processed/` folder.

The chunking job will run after the ingestion job in the production pipeline.

---

## 1. Open the Chunking Script

Open:

```text
src/chunk/run_chunk.py
```

---

## 2. Add the Chunking Code

Paste the PDF chunking code into:

```text
src/chunk/run_chunk.py
```

The script will:

1. Read PDF files from `raw/`
2. Extract text page by page
3. Split text into overlapping chunks
4. Add metadata to each chunk
5. Save chunk records as JSONL files in `processed/`

---

## 3. Verify Required Imports

The chunking script uses:

```python
from pypdf import PdfReader

from src.common.gcs_utils import (
    download_bytes,
    list_blobs,
    upload_text,
)

from src.common.settings import settings
```

---

## 4. Run the Chunking Job Locally

From the project root:

```powershell
python -m src.chunk.run_chunk
```

---

## 5. Expected Output

Example:

```text
Found PDFs: 12

Chunking: gs://undp-project-documents-llm-prod/raw/year=2026/country=Lebanon/project_id=01003798/3406425_Project_Document__ProDoc_.pdf

Created chunks: 109

Chunking complete.

Total PDFs processed: 12
Total chunks created: 1427
```

---

## 6. Verify Processed Files

List the processed files:

```powershell
gcloud storage ls gs://undp-project-documents-llm-prod/processed/ --recursive
```

Example:

```text
gs://undp-project-documents-llm-prod/processed/year=2026/country=Lebanon/project_id=01003798/3406425_Project_Document__ProDoc_.pdf.jsonl
```

---

## 7. Verify Chunk Content

Download one processed file:

```powershell
gcloud storage cp `
gs://undp-project-documents-llm-prod/processed/year=2026/country=Lebanon/project_id=01003798/3406425_Project_Document__ProDoc_.pdf.jsonl `
sample_chunks.jsonl
```

Inspect the first lines:

```powershell
Get-Content sample_chunks.jsonl -Head 3
```

Example:

```json
{"source_pdf_blob":"raw/...pdf","page_number":1,"chunk_index":1,"text":"..."}
{"source_pdf_blob":"raw/...pdf","page_number":1,"chunk_index":2,"text":"..."}
{"source_pdf_blob":"raw/...pdf","page_number":2,"chunk_index":1,"text":"..."}
```

---

## Output Structure

After processing:

```text
raw/
└── year=2026/
    └── country=Lebanon/
        └── project_id=01003798/
            └── document.pdf

processed/
└── year=2026/
    └── country=Lebanon/
        └── project_id=01003798/
            └── document.pdf.jsonl
```

---

## What the Chunking Job Produces

Each chunk contains:

| Field           | Description                  |
| --------------- | ---------------------------- |
| source_pdf_blob | Original PDF location in GCS |
| page_number     | PDF page number              |
| chunk_index     | Chunk number within the page |
| text            | Chunk text                   |
| created_at      | Processing timestamp         |

---

## Production Pipeline Flow

```text
UNDP API
    ↓
Ingestion Job
    ↓
raw/
    ↓
Chunking Job
    ↓
processed/
    ↓
Embedding Job
    ↓
embeddings/
    ↓
Gemini RAG Chatbot
```

Once chunk files are successfully created in `processed/`, continue to **Step 8 — Add the Embedding Job**.
# Step 8 — Add the Embedding Job

This step generates vector embeddings from the PDF chunks stored in Google Cloud Storage and saves the embeddings back to GCS for retrieval during question answering.

---

# Purpose

The chunking step converted PDF pages into text chunks and stored them in:

```text
processed/
```

The embedding step converts each chunk into a numeric vector representation using:

```text
gemini-embedding-001
```

These vectors allow semantic search to find relevant information even when the user's question does not exactly match the document wording.

---

# Input

The embedding job reads JSONL files from:

```text
gs://undp-project-documents-llm-prod/processed/
```

Each record looks similar to:

```json
{
  "source_pdf_blob": "...",
  "page_number": 12,
  "chunk_index": 3,
  "text": "UNDP supports digital transformation..."
}
```

---

# Output

The job creates embedding files under:

```text
gs://undp-project-documents-llm-prod/embeddings/
```

Example:

```text
embeddings/year=2026/country=Lebanon/project_id=01003798/3406425_Project_Document_ProDoc_.pdf.jsonl
```

Each record contains:

```json
{
  "source_pdf_blob": "...",
  "page_number": 12,
  "chunk_index": 3,
  "text": "...",
  "embedding": [...],
  "embedding_model": "gemini-embedding-001",
  "embedded_at": "2026-06-13T23:15:00Z"
}
```

---

# File Location

Create:

```text
src/embed/run_embed.py
```

---

# How the Job Works

| Step | Description                          |
| ---- | ------------------------------------ |
| 1    | Read chunk files from GCS            |
| 2    | Parse JSONL records                  |
| 3    | Send chunk text to Gemini Embeddings |
| 4    | Receive embedding vectors            |
| 5    | Attach vectors to metadata           |
| 6    | Save embedding records to GCS        |
| 7    | Repeat for all chunk files           |

---

# Run Locally

From the project root:

```powershell
python -m src.embed.run_embed
```

---

# Expected Output

```text
Starting embedding job...
Gemini client created

Found chunk files: 12

Embedding: gs://undp-project-documents-llm-prod/processed/...
Created embeddings: 344

Embedding: gs://undp-project-documents-llm-prod/processed/...
Created embeddings: 17

Embedding: gs://undp-project-documents-llm-prod/processed/...
Created embeddings: 96

Embedding complete.
Total chunk files processed: 12
Total embeddings created: 1162
```

---

# Verify Embeddings

List generated embedding files:

```powershell
gcloud storage ls gs://undp-project-documents-llm-prod/embeddings/ --recursive
```

You should see files similar to:

```text
gs://undp-project-documents-llm-prod/embeddings/year=2026/country=Lebanon/project_id=01003798/3406425_Project_Document_ProDoc_.pdf.jsonl
```

---

# Why Embeddings Are Needed

A user may ask:

```text
What digital initiatives are supported in Lebanon?
```

The documents may contain:

```text
digital transformation
e-governance
data platforms
digital public services
```

Embeddings place related concepts close together in vector space, allowing retrieval even when the wording differs.

---

# Next Step

After embeddings are generated, the next step is:

```text
Step 9 — Build the Retrieval and Question Answering Pipeline
```

# Step 9 — Retrieval and Question Answering Pipeline

## Objective

Build the Retrieval-Augmented Generation (RAG) pipeline that:

1. Receives a user question.
2. Generates a query embedding.
3. Loads document embeddings from Google Cloud Storage.
4. Finds the most relevant chunks.
5. Builds a context from retrieved chunks.
6. Sends the context to Gemini.
7. Returns a grounded answer.

---

# Architecture

```text
User Question
      │
      ▼
Gemini Query Embedding
      │
      ▼
Load Document Embeddings
      │
      ▼
Cosine Similarity Search
      │
      ▼
Top K Chunks
      │
      ▼
Build Context
      │
      ▼
Gemini 2.5 Flash
      │
      ▼
Answer
```

---

# Project Structure

Create the following files:

```text
src/
├── retrieval/
│   ├── __init__.py
│   └── retriever.py
│
├── chatbot/
│   ├── app.py
│   └── qa.py
│
scripts/
└── test_rag.py
```

---

# Retriever Module

File:

```text
src/retrieval/retriever.py
```

Responsibilities:

* Load embeddings from GCS
* Generate query embeddings
* Calculate cosine similarity
* Rank document chunks
* Remove duplicate chunks
* Return the top K results

---

# Loading Embeddings

Read embedding files from:

```text
gs://undp-project-documents-llm-prod/embeddings/
```

Each embedding record contains:

```json
{
  "text": "...",
  "embedding": [...],
  "page_number": 12,
  "source_pdf_blob": "...",
  "embedding_model": "gemini-embedding-001"
}
```

---

# Query Embedding

Generate question embeddings using:

```text
gemini-embedding-001
```

Configuration:

```python
task_type="RETRIEVAL_QUERY"
output_dimensionality=768
```

This matches the embedding configuration used during document embedding.

---

# Similarity Search

For each document chunk:

1. Compute cosine similarity between the query embedding and document embedding.
2. Sort results by similarity score.
3. Select the highest scoring chunks.

Formula:

```text
cosine_similarity =
dot(query_embedding, document_embedding)
/
(
||query_embedding||
*
||document_embedding||
)
```

---

# Duplicate Removal

Some documents appear multiple times across different years.

To avoid returning identical content multiple times, apply deduplication using chunk text:

```python
key = record["text"][:300]
```

Only unique chunks are returned.

---

# Question Answering Module

File:

```text
src/chatbot/qa.py
```

Responsibilities:

1. Call the retriever.
2. Build a context from retrieved chunks.
3. Create the Gemini prompt.
4. Generate the answer.

Prompt structure:

```text
You are a UNDP project assistant.

Answer only using the provided context.

Context:
...

Question:
...
```

---

# Test Script

File:

```text
scripts/test_rag.py
```

Purpose:

* Validate retrieval
* Validate Gemini answer generation
* Test the complete RAG pipeline locally

Run:

```powershell
python -m scripts.test_rag
```

---

# Example Question

```text
What digital initiatives are supported in Lebanon?
```

Example answer:

```text
Technical support is provided for digital solution design.
```

The answer is generated from retrieved document content rather than model knowledge.

---

# Verification

Run:

```powershell
python -m scripts.test_rag
```

Expected output:

```text
QUESTION
--------
What digital initiatives are supported in Lebanon?

ANSWER
------
...
```

To inspect retrieval results, temporarily print:

```python
chunks = retrieve(question)

for chunk in chunks:
    print(chunk["score"])
    print(chunk["text"][:500])
```

---

# Current Dataset

```text
PDFs: 12

Chunk Files: 12

Embedded Files: 6

Total Chunks: 1162
```

Files with no extracted text were skipped during embedding.

---

# Deliverables

After completing this step:

* Retrieval pipeline implemented
* Query embeddings generated with Gemini
* Cosine similarity search implemented
* Duplicate retrieval results removed
* Gemini answer generation implemented
* End-to-end RAG pipeline validated

---

# Next Step

Proceed to:

```text
Step 10 — Build the Streamlit Chat Application
```


# Step 10 — Build the Streamlit Chat Application

## Objective

Build a web-based interface that allows users to interact with the Retrieval-Augmented Generation (RAG) pipeline.

The application:

1. Accepts user questions.
2. Retrieves relevant document chunks.
3. Generates answers using Gemini.
4. Displays the generated answer.
5. Displays the retrieved sources used to generate the answer.

---

# Architecture

```text
User
  │
  ▼
Streamlit Web Application
  │
  ▼
Question Answering Module
  │
  ▼
Retriever
  │
  ▼
Embeddings Stored in GCS
  │
  ▼
Top K Chunks
  │
  ▼
Gemini 2.5 Flash
  │
  ▼
Answer + Sources
```

---

# Project Structure

The chatbot application is implemented in:

```text
src/
├── chatbot/
│   ├── app.py
│   └── qa.py
│
├── retrieval/
│   └── retriever.py
│
├── common/
│   ├── settings.py
│   └── gcs_utils.py
```

---

# Streamlit Application

File:

```text
src/chatbot/app.py
```

Responsibilities:

* Render the user interface
* Accept user questions
* Call the question answering module
* Display answers
* Display retrieved sources

---

# Question Answering Module

File:

```text
src/chatbot/qa.py
```

The `ask()` function:

1. Retrieves relevant chunks.
2. Builds context.
3. Sends the context to Gemini.
4. Returns:

```python
answer, chunks
```

This allows the application to display both the generated answer and the supporting sources.

---

# Source Display

Each retrieved chunk is displayed with:

* Similarity score
* Page number
* Source file
* Retrieved text

Example:

```text
Source 1 | Score: 0.6957

Page Number: 24

Source File:
raw/year=2026/country=Lebanon/...

Retrieved Text:
...
```

This makes the generated answer traceable to the original documents.

---

# Run Locally

From the project root:

```powershell
$env:PYTHONPATH="."
streamlit run src/chatbot/app.py
```

---

# Example Question

```text
What digital initiatives are supported in Lebanon?
```

Example answer:

```text
The LHSP 2.0 project provides technical support for digital solution design.
```

---

# Example Source

```text
Source 1

Score: 0.6908

Technical support is provided for:

- Product development
- Digital solution design
- Climate resilience
- Recycling solutions
```

---

# Verification

Verify that:

1. The Streamlit page loads successfully.
2. Questions can be submitted.
3. Answers are generated.
4. Sources are displayed.
5. Similarity scores are shown.
6. Retrieved text matches the generated answer.

---

# Deliverables

After completing this step:

* Streamlit web application implemented
* Question submission interface available
* Gemini answer generation integrated
* Source display implemented
* Retrieval transparency enabled
* End-to-end RAG application functional

---

# Current Workflow

```text
UNDP API
      ↓
PDF Documents
      ↓
Chunking
      ↓
Gemini Embeddings
      ↓
Embeddings Stored in GCS
      ↓
Retriever
      ↓
Top K Chunks
      ↓
Gemini 2.5 Flash
      ↓
Streamlit Interface
      ↓
Answer + Sources
```

---

# Next Step

Proceed to:

```text
Step 11 — Containerize and Deploy the Chatbot to Cloud Run
```
# Step 11 — Containerize and Deploy the Chatbot to Cloud Run

## Objective

Deploy the Streamlit-based UNDP RAG chatbot to Google Cloud Run.

Project Information:

```text
Project Name: undp-project-documents
Project ID: undp-project-documents
Project Number: 1097805338474
Region: northamerica-northeast1
Bucket: undp-project-documents-llm-prod
```

---

# 1. Verify Active Project

```powershell
gcloud config get-value project
```

Expected:

```text
undp-project-documents
```

If needed:

```powershell
gcloud config set project undp-project-documents
```

---

# 2. Authenticate

Login to Google Cloud:

```powershell
gcloud auth login
```

Configure Application Default Credentials:

```powershell
gcloud auth application-default login
```

Verify:

```powershell
gcloud auth list
```

---

# 3. Enable Required APIs

```powershell
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

---

# 4. Configure IAM Permissions

## Cloud Build Builder

Required for Cloud Build to create and deploy containers.

```powershell
gcloud projects add-iam-policy-binding undp-project-documents ^
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" ^
  --role="roles/cloudbuild.builds.builder"
```

---

## Vertex AI Access

Required for Gemini embedding generation and answer generation.

```powershell
gcloud projects add-iam-policy-binding undp-project-documents ^
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" ^
  --role="roles/aiplatform.user"
```

---

## Cloud Storage Access

Required to read:

```text
raw/
processed/
embeddings/
metadata/
```

inside the bucket.

```powershell
gcloud projects add-iam-policy-binding undp-project-documents ^
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" ^
  --role="roles/storage.objectViewer"
```

---

# 5. Create Dockerfile

Create:

```text
Dockerfile
```

Add:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install uv

RUN uv sync

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["streamlit", "run", "src/chatbot/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

---

# 6. Verify Dependencies

Run:

```powershell
uv sync
```

Update lock file:

```powershell
uv lock
```

Verify:

```text
uv.lock
```

exists in the project root.

---

# 7. Test Streamlit Locally

Run:

```powershell
$env:PYTHONPATH="."
streamlit run src/chatbot/app.py
```

Verify:

* Application loads
* Questions can be submitted
* Answers are generated
* Sources are displayed

---

# 8. Build Docker Image

Build:

```powershell
docker build -t undp-chatbot .
```

Verify image:

```powershell
docker images
```

Run locally:

```powershell
docker run -p 8080:8080 undp-chatbot
```

Open:

```text
http://localhost:8080
```

Verify the chatbot works correctly.

---

# 9. Deploy to Cloud Run

Deploy directly from source:

```powershell
gcloud run deploy undp-chatbot ^
  --source . ^
  --region northamerica-northeast1 ^
  --allow-unauthenticated
```

Cloud Build will:

1. Build the container image
2. Store the image in Artifact Registry
3. Deploy the service to Cloud Run

---

# 10. Verify Deployment

List services:

```powershell
gcloud run services list --region northamerica-northeast1
```

Retrieve URL:

```powershell
gcloud run services describe undp-chatbot ^
  --region northamerica-northeast1 ^
  --format="value(status.url)"
```

Example:

```text
https://undp-chatbot-xxxxxxxxxx-nn.a.run.app
```

Open the URL and verify:

* Application loads
* Questions can be submitted
* Sources are displayed
* Gemini answers are generated

---

# Troubleshooting

## Cloud Build Permission Error

Run:

```powershell
gcloud projects add-iam-policy-binding undp-project-documents ^
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" ^
  --role="roles/cloudbuild.builds.builder"
```

---

## Vertex AI Permission Error

Run:

```powershell
gcloud projects add-iam-policy-binding undp-project-documents ^
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" ^
  --role="roles/aiplatform.user"
```

---

## Storage Permission Error

Run:

```powershell
gcloud projects add-iam-policy-binding undp-project-documents ^
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" ^
  --role="roles/storage.objectViewer"
```

---

## Import Errors

Verify Dockerfile contains:

```dockerfile
ENV PYTHONPATH=/app
```

and all imports use:

```python
from src.chatbot.qa import ask
```

```python
from src.retrieval.retriever import retrieve
```

```python
from src.common.settings import settings
```

---

# Deliverables

After completing this step:

* Docker image created
* Cloud Build configured
* Artifact Registry configured automatically
* Cloud Run service deployed
* Vertex AI access configured
* Cloud Storage access configured
* Public chatbot URL available

---

# Next Step

Proceed to:

```text
Step 12 — Build the Cloud Composer Pipeline
```

The Composer workflow will orchestrate:

1. Ingestion Job
2. Chunking Job
3. Embedding Job
4. Cloud Run deployment updates


