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

# 5. Create Dockerfile for the Chatbot

Use the existing chatbot Dockerfile:

```text
docker/Dockerfile.chatbot
```

Do not create a separate root `Dockerfile` yet.

Update `docker/Dockerfile.chatbot` with:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install uv

RUN uv sync

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uv", "run", "streamlit", "run", "src/chatbot/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

The command uses:

```text
uv run streamlit
```

because `uv sync` installs project dependencies inside the project virtual environment. Calling `streamlit` directly can fail inside Docker.

---

# 6. Verify Dependencies

Run:

```powershell
uv sync
```

Update the lock file:

```powershell
uv lock
```

Verify that this file exists in the project root:

```text
uv.lock
```

Required dependencies include:

```text
streamlit
google-genai
google-cloud-storage
numpy
python-dotenv
requests
pypdf
```

---

# 7. Test Streamlit Locally Without Docker

Run from the project root:

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

# 8. Build Docker Image Locally

Build the chatbot image using the custom Dockerfile:

```powershell
docker build -f docker/Dockerfile.chatbot -t undp-chatbot .
```

Verify the image exists:

```powershell
docker images
```

---

# 9. Run Docker Locally With Google Credentials

The chatbot needs access to:

* Google Cloud Storage
* Vertex AI Gemini

When running locally inside Docker, mount your local Google Application Default Credentials.

First make sure ADC exists locally:

```powershell
gcloud auth application-default login
```

Then run the container:

```powershell
docker run -p 8080:8080 `
  -e GOOGLE_APPLICATION_CREDENTIALS=/gcloud/application_default_credentials.json `
  -v "$env:APPDATA\gcloud:/gcloud" `
  undp-chatbot
```

Open:

```text
http://localhost:8080
```

Verify:

* Application loads
* Questions can be submitted
* Answers are generated
* Sources are displayed

---

# 10. Prepare for Cloud Run Deployment

Cloud Run source deployment expects a `Dockerfile` in the project root.

Copy the chatbot Dockerfile to the root:

```powershell
Copy-Item docker\Dockerfile.chatbot Dockerfile
```

Verify:

```powershell
dir Dockerfile
```

---

# 11. Deploy to Cloud Run

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

# 12. Verify Deployment

List Cloud Run services:

```powershell
gcloud run services list --region northamerica-northeast1
```

Retrieve the service URL:

```powershell
gcloud run services describe undp-chatbot ^
  --region northamerica-northeast1 ^
  --format="value(status.url)"
```

Open the URL in a browser.

Verify:

* Application loads
* Questions can be submitted
* Sources are displayed
* Gemini answers are generated

without retrieving url I got this at end of deployment :

(undp_pipeline_prod) PS C:\Users\mirei\OneDrive\Desktop\LLMproject\undp_pipeline_prod> gcloud run deploy undp-chatbot --source . --region northamerica-northeast1 --allow-unauthenticated
Building using Dockerfile and deploying container to Cloud Run service [undp-chatbot] in project [undp-project-documents] region [northamerica-northeast1]
OK Building and deploying... Done.                                                                                        
  OK Validating configuration...                                                                                          
  OK Uploading sources...                                                                                                 
  OK Building Container... Logs are available at [ https://console.cloud.google.com/cloud-build/builds;region=northamerica
  -northeast1/3e858d39-53d5-4a64-8842-e0de54a362cc?project=1097805338474 ].                                               
  OK Creating Revision...                                                                                                 
  OK Routing traffic...                                                                                                   
  OK Setting IAM Policy...                                                                                                
Done.                                                                                                                     
Service [undp-chatbot] revision [undp-chatbot-00003-l6f] has been deployed and is serving 100 percent of traffic.
Service URL: https://undp-chatbot-1097805338474.northamerica-northeast1.run.app
(undp_pipeline_prod) PS C:\Users\mirei\OneDrive\Desktop\LLMproject\undp_pipeline_prod> 


# Deliverables

After completing this step:

* Chatbot Dockerfile updated
* Docker image built locally
* Docker container tested locally
* Google credentials mounted for local Docker testing
* Cloud Run deployment prepared
* Public Cloud Run service deployed
* Sources and answers verified in the deployed application

---
this is a personal portfolio project

I would not use Composer.

I would use:

Cloud Scheduler
      ↓
Cloud Workflows
      ↓
Cloud Run Job: ingest
      ↓
Cloud Run Job: chunk
      ↓
Cloud Run Job: embed

Cost:

Usually under $10/month

for a weekly pipeline.

"For enterprise-scale orchestration this pipeline can be migrated to Cloud Composer (Airflow)."

The pipeline is orchestrated using Cloud Scheduler and Cloud Run Jobs.

Cloud Scheduler triggers the ingestion job on a weekly schedule.

The ingestion job downloads UNDP project PDFs and stores them in Google Cloud Storage.

The chunking job processes PDFs into text chunks.

The embedding job generates vector embeddings and stores them in Google Cloud Storage.

The Streamlit chatbot retrieves relevant chunks and uses Gemini to generate answers.

For enterprise-scale orchestration with complex dependencies and monitoring requirements, this architecture can be migrated to Cloud Composer (Apache Airflow).

Updated Architecture Diagram

```
                 ┌─────────────────┐
                 │  Cloud Scheduler │
                 └────────┬────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Cloud Run Job     │
                │ undp-ingest-job   │
                └────────┬──────────┘
                         │
                         ▼
                   GCS raw/
                         │
                         ▼
                ┌───────────────────┐
                │ Cloud Run Job     │
                │ undp-chunk-job    │
                └────────┬──────────┘
                         │
                         ▼
                GCS processed/
                         │
                         ▼
                ┌───────────────────┐
                │ Cloud Run Job     │
                │ undp-embed-job    │
                └────────┬──────────┘
                         │
                         ▼
               GCS embeddings/
                         │
                         ▼
                ┌───────────────────┐
                │ Streamlit Chatbot │
                │ Gemini + RAG      │
                └───────────────────┘

                ```

               One small improvement: instead of having Scheduler trigger only the ingest job and somehow chain the others, I would use:

Cloud Scheduler
      ↓
Cloud Workflows
      ↓
ingest-job
      ↓
chunk-job
      ↓
embed-job

because Google Cloud Workflows is lightweight, inexpensive, and designed specifically to execute steps sequentially. It gives you most of the orchestration benefits of Airflow without the Composer cost.

So my preferred final architecture for your UNDP project would be:

Architecture

Cloud Scheduler
      ↓
Cloud Workflows
      ↓
Cloud Run Job: ingest
      ↓
Cloud Run Job: chunk
      ↓
Cloud Run Job: embed
      ↓
Google Cloud Storage
      ↓
Streamlit Chatbot



New architecture:

Replace only the orchestration folder/docs:

Remove / ignore:
dags/
dags/undp_pipeline_dag.py
Composer instructions

Add:
workflows/
workflows/undp_pipeline_workflow.yaml
scheduler/
scheduler/create_weekly_schedule.md

Recommended folder structure:

undp_pipeline_prod/
│
├── docker/
│   ├── Dockerfile.ingest
│   ├── Dockerfile.chunk
│   ├── Dockerfile.embed
│   └── Dockerfile.chatbot
│
├── src/
│   ├── ingest/
│   │   └── run_ingest.py
│   ├── chunk/
│   │   └── run_chunk.py
│   ├── embed/
│   │   └── run_embed.py
│   └── chatbot/
│       └── app.py
│
├── workflows/
│   └── undp_pipeline_workflow.yaml
│
├── scheduler/
│   └── create_weekly_schedule.md
│
├── docs/
│   ├── 01_setup.md
│   ├── 02_cloud_run_jobs.md
│   ├── 03_workflows_scheduler.md
│   └── 04_deploy_chatbot.md
│
├── pyproject.toml
├── uv.lock
├── README.md
└── .gitignore

# Build and Push Docker Images

This step packages each pipeline component into a Docker image and uploads it to Google Artifact Registry.

## Architecture

```text
Local Source Code
        ↓
Docker Image
        ↓
Artifact Registry
        ↓
Cloud Run Job
```

The UNDP pipeline contains three Cloud Run Jobs:

```text
undp-ingest-job
undp-chunk-job
undp-embed-job
```

Each job has its own Docker image.

---

## Prerequisites

Verify Docker is running:

```powershell
docker --version
```

Verify the correct GCP project:

```powershell
gcloud config get-value project
```

Expected:

```text
undp-project-documents
```

Authenticate Docker with Artifact Registry:

```powershell
gcloud auth configure-docker northamerica-northeast1-docker.pkg.dev
```

Answer:

```text
Y
```

---

## Build and Push Ingest Image

Build:

```powershell
docker build -f docker/Dockerfile.ingest `
  -t northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest .
```

Push:

```powershell
docker push northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest
```

---

## Build and Push Chunk Image

Build:

```powershell
docker build -f docker/Dockerfile.chunk `
  -t northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-chunk:latest .
```

Push:

```powershell
docker push northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-chunk:latest
```

---

## Build and Push Embed Image

Build:

```powershell
docker build -f docker/Dockerfile.embed `
  -t northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-embed:latest .
```

Push:

```powershell
docker push northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-embed:latest
```

---

## Verify Images

List images stored in Artifact Registry:

```powershell
gcloud artifacts docker images list `
  northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline
```

Expected images:

```text
undp-ingest
undp-chunk
undp-embed
```

---

## Troubleshooting

### Push appears stuck

Wait several minutes.

If still stuck:

```powershell
Ctrl + C
```

Re-authenticate Docker:

```powershell
gcloud auth configure-docker northamerica-northeast1-docker.pkg.dev
```

Retry the push command.

### Permission denied

Verify Artifact Registry permissions:

```powershell
gcloud auth list
```

Verify project:

```powershell
gcloud config get-value project
```

Expected:

```text
undp-project-documents
```

---

## Deliverables

After completing this step:

```text
Artifact Registry
└── undp-pipeline
    ├── undp-ingest:latest
    ├── undp-chunk:latest
    └── undp-embed:latest
```

These images are now ready to be deployed as Cloud Run Jobs.
# Create Cloud Run Jobs

This step deploys the UNDP pipeline Docker images as Cloud Run Jobs.

Cloud Run Jobs are designed for batch workloads that start, execute, and exit.

The pipeline contains three jobs:

```text
undp-ingest-job
undp-chunk-job
undp-embed-job
```

---

# Architecture

```text
Artifact Registry
        │
        ▼
Cloud Run Job: ingest
        │
        ▼
Cloud Run Job: chunk
        │
        ▼
Cloud Run Job: embed
```

Each job executes a single step of the pipeline.

---

# Prerequisites

Verify the Docker images exist in Artifact Registry:

```powershell
gcloud artifacts docker images list `
  northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline
```

Expected images:

```text
undp-ingest
undp-chunk
undp-embed
```

---

# Deploy Ingestion Job

```powershell
gcloud run jobs deploy undp-ingest-job `
  --image northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest `
  --region northamerica-northeast1
```

Expected result:

```text
Job [undp-ingest-job] successfully deployed.
```

---

# Deploy Chunking Job

```powershell
gcloud run jobs deploy undp-chunk-job `
  --image northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-chunk:latest `
  --region northamerica-northeast1
```

Expected result:

```text
Job [undp-chunk-job] successfully deployed.
```

---

# Deploy Embedding Job

```powershell
gcloud run jobs deploy undp-embed-job `
  --image northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-embed:latest `
  --region northamerica-northeast1
```

Expected result:

```text
Job [undp-embed-job] successfully deployed.
```

---

# Verify Jobs

List all jobs:

```powershell
gcloud run jobs list `
  --region northamerica-northeast1
```

Expected:

```text
undp-ingest-job
undp-chunk-job
undp-embed-job
```

---

# Test Ingestion Job

Run:

```powershell
gcloud run jobs execute undp-ingest-job `
  --region northamerica-northeast1 `
  --wait
```

Expected behavior:

```text
Fetch UNDP projects
Download new PDFs
Upload PDFs to GCS
Create metadata file
```

---

# Test Chunking Job

Run:

```powershell
gcloud run jobs execute undp-chunk-job `
  --region northamerica-northeast1 `
  --wait
```

Expected behavior:

```text
Read PDFs from GCS
Create text chunks
Upload JSONL chunk files
Skip already processed PDFs
```

---

# Test Embedding Job

Run:

```powershell
gcloud run jobs execute undp-embed-job `
  --region northamerica-northeast1 `
  --wait
```

Expected behavior:

```text
Read chunk files
Generate Gemini embeddings
Upload embeddings to GCS
Skip already embedded files
```

---

# View Execution Logs

List executions:

```powershell
gcloud run jobs executions list `
  --job undp-ingest-job `
  --region northamerica-northeast1
```

Describe an execution:

```powershell
gcloud run jobs executions describe EXECUTION_NAME `
  --region northamerica-northeast1
```

Open logs:

```powershell
gcloud logging read `
  "resource.type=cloud_run_job" `
  --limit=50
```

---

# Verify Output in GCS

Expected bucket structure:

```text
gs://undp-project-documents-llm-2026/

raw/
processed/
embeddings/
metadata/
```

Expected contents:

```text
raw/
    PDF documents

processed/
    JSONL chunk files

embeddings/
    Embedded JSONL files

metadata/
    Ingestion metadata CSV files
```

---

# Deliverables

After completing this step:

```text
Cloud Run Jobs

✓ undp-ingest-job
✓ undp-chunk-job
✓ undp-embed-job
```

The pipeline components are now deployed and ready for orchestration using Cloud Workflows and Cloud Scheduler.


# Step 13 — # Cloud Workflows and Cloud Scheduler

This step connects the UNDP pipeline components into a fully automated workflow.

The workflow executes:

```text
undp-ingest-job
      ↓
undp-chunk-job
      ↓
undp-embed-job
```

Cloud Scheduler will later trigger the workflow automatically on a schedule.

---

# Architecture

```text
Cloud Scheduler
      ↓
Cloud Workflow
      ↓
Cloud Run Job: ingest
      ↓
Cloud Run Job: chunk
      ↓
Cloud Run Job: embed
      ↓
Google Cloud Storage
      ↓
Streamlit Chatbot
```

---

# Create Workflow Definition

File:

```text
workflows/undp_pipeline_workflow.yaml
```

Content:

```yaml
main:
  steps:

    - ingest:
        call: googleapis.run.v1.namespaces.jobs.run
        args:
          name: namespaces/1097805338474/jobs/undp-ingest-job
          location: northamerica-northeast1

    - chunk:
        call: googleapis.run.v1.namespaces.jobs.run
        args:
          name: namespaces/1097805338474/jobs/undp-chunk-job
          location: northamerica-northeast1

    - embed:
        call: googleapis.run.v1.namespaces.jobs.run
        args:
          name: namespaces/1097805338474/jobs/undp-embed-job
          location: northamerica-northeast1

    - done:
        return: "UNDP pipeline completed successfully"
```

---

# Enable Workflows API

```powershell
gcloud services enable workflows.googleapis.com
```

---

# Deploy Workflow

```powershell
gcloud workflows deploy undp-pipeline-workflow `
  --source=workflows/undp_pipeline_workflow.yaml `
  --location=northamerica-northeast1
```

Expected result:

```text
state: ACTIVE
```

---

# Configure IAM Permissions

Grant Cloud Run permissions:

```powershell
gcloud projects add-iam-policy-binding undp-project-documents `
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" `
  --role="roles/run.developer"
```

```powershell
gcloud projects add-iam-policy-binding undp-project-documents `
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" `
  --role="roles/run.viewer"
```

```powershell
gcloud projects add-iam-policy-binding undp-project-documents `
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" `
  --role="roles/run.admin"
```

Allow the workflow service account to act as a service account:

```powershell
gcloud iam service-accounts add-iam-policy-binding `
  1097805338474-compute@developer.gserviceaccount.com `
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" `
  --role="roles/iam.serviceAccountUser"
```

---

# Run Workflow Manually

```powershell
gcloud workflows run undp-pipeline-workflow `
  --location=northamerica-northeast1
```

Successful result:

```text
state: SUCCEEDED
result: "UNDP pipeline completed successfully"
```

Example:

```text
duration: 55.31s
state: SUCCEEDED
```

---

# View Workflow Executions

List executions:

```powershell
gcloud workflows executions list undp-pipeline-workflow `
  --location=northamerica-northeast1
```

Describe a specific execution:

```powershell
gcloud workflows executions describe EXECUTION_ID `
  --workflow=undp-pipeline-workflow `
  --location=northamerica-northeast1
```

---

# Verify Pipeline Execution

The workflow should execute:

```text
undp-ingest-job
```

Downloads new UNDP PDFs.

```text
undp-chunk-job
```

Creates chunk files.

```text
undp-embed-job
```

Creates Gemini embeddings.

Verify outputs:

```text
gs://undp-project-documents-llm-prod/raw/
gs://undp-project-documents-llm-prod/processed/
gs://undp-project-documents-llm-prod/embeddings/
gs://undp-project-documents-llm-prod/metadata/
```

---

# Deliverables

After completing this step:

```text
✓ Cloud Workflow deployed

✓ Workflow state = ACTIVE

✓ Workflow execution state = SUCCEEDED

✓ Cloud Run Jobs orchestrated automatically

✓ End-to-end pipeline execution verified
```

---

# Next Step

Create a Cloud Scheduler job to automatically execute the workflow every week.

Target architecture:

```text
Cloud Scheduler
      ↓
Cloud Workflow
      ↓
undp-ingest-job
      ↓
undp-chunk-job
      ↓
undp-embed-job
      ↓
Google Cloud Storage
      ↓
Streamlit Chatbot
```


# Step  14:

# Create Cloud Scheduler (Daily Execution)

This step automates the UNDP pipeline by triggering the Cloud Workflow every day.

Current schedule:

```text
Daily
```

The schedule can later be changed to:

```text
Weekly
```

without changing the workflow or Cloud Run Jobs.

---

# Architecture

```text
Cloud Scheduler
      ↓
Cloud Workflow
      ↓
undp-ingest-job
      ↓
undp-chunk-job
      ↓
undp-embed-job
      ↓
Google Cloud Storage
      ↓
Streamlit Chatbot
```

---

# Enable Cloud Scheduler API

```powershell
gcloud services enable cloudscheduler.googleapis.com
```

Verify:

```powershell
gcloud services list --enabled | findstr scheduler
```

Expected:

```text
cloudscheduler.googleapis.com
```

---

# Create Scheduler Service Account

Create a dedicated service account:

```powershell
gcloud iam service-accounts create scheduler-sa `
  --display-name="UNDP Scheduler Service Account"
```

Result:

```text
scheduler-sa@undp-project-documents.iam.gserviceaccount.com
```

---

# Grant Workflow Invoker Permission

Allow Cloud Scheduler to execute the workflow:

```powershell
gcloud projects add-iam-policy-binding undp-project-documents `
  --member="serviceAccount:scheduler-sa@undp-project-documents.iam.gserviceaccount.com" `
  --role="roles/workflows.invoker"
```

---

# Create Daily Scheduler Job

Run every day at 6:00 AM Montreal time:

```powershell
gcloud scheduler jobs create http undp-daily-pipeline `
  --location=northamerica-northeast1 `
  --schedule="0 6 * * *" `
  --time-zone="America/Montreal" `
  --uri="https://workflowexecutions.googleapis.com/v1/projects/undp-project-documents/locations/northamerica-northeast1/workflows/undp-pipeline-workflow/executions" `
  --http-method=POST `
  --oauth-service-account-email="scheduler-sa@undp-project-documents.iam.gserviceaccount.com"
```

Cron expression:

```text
0 6 * * *
```

Meaning:

```text
Minute: 0
Hour: 6
Every day
```

---

# Test Scheduler Immediately

Run manually:

```powershell
gcloud scheduler jobs run undp-daily-pipeline `
  --location=northamerica-northeast1
```

---

# Verify Scheduler Job

List jobs:

```powershell
gcloud scheduler jobs list `
  --location=northamerica-northeast1
```

Expected:

```text
undp-daily-pipeline
```

Describe job:

```powershell
gcloud scheduler jobs describe undp-daily-pipeline `
  --location=northamerica-northeast1
```

Expected:

```text
state: ENABLED
```

---

# Verify Workflow Execution

List workflow executions:

```powershell
gcloud workflows executions list undp-pipeline-workflow `
  --location=northamerica-northeast1
```

Expected:

```text
state: SUCCEEDED
```

---

# Change to Weekly Later

When ready to reduce costs:

```powershell
gcloud scheduler jobs update http undp-daily-pipeline `
  --location=northamerica-northeast1 `
  --schedule="0 6 * * 1"
```

Weekly cron:

```text
0 6 * * 1
```

Meaning:

```text
Every Monday
06:00 AM
```

---

# Deliverables

After completing this step:

```text
✓ Cloud Scheduler enabled

✓ Daily schedule configured

✓ Workflow automatically executed

✓ Ingestion automated

✓ Chunking automated

✓ Embedding automated

✓ End-to-end UNDP pipeline fully automated
```

---

# Final Production Architecture

```text
UNDP API
    ↓
Cloud Scheduler
    ↓
Cloud Workflow
    ↓
Cloud Run Job: ingest
    ↓
Cloud Run Job: chunk
    ↓
Cloud Run Job: embed
    ↓
Google Cloud Storage
    ↓
Streamlit Cloud Run Chatbot
```

This architecture is suitable for a personal production deployment and can later be migrated to Cloud Composer (Apache Airflow) if enterprise-scale orchestration is required.





Future Improvements

Potential production enhancements:

• Weekly schedule instead of daily
• Email alerts on failures
• Monitoring dashboards
• CI/CD with Cloud Build
• Vector database integration
• Cloud Composer migration for enterprise orchestration


# step 16

# Future Improvement: CI/CD with Cloud Build

## Overview

The current deployment process for the UNDP pipeline is manual. After making code changes, Docker images must be rebuilt, pushed to Artifact Registry, and Cloud Run Jobs must be updated.

A future improvement is to implement Continuous Integration and Continuous Deployment (CI/CD) using Google Cloud Build.

This would automate the deployment process whenever code is pushed to GitHub.

---

# Current Deployment Process

Today, deployment requires manually executing the following steps:

```text
Code Change
    ↓
docker build
    ↓
docker push
    ↓
gcloud run jobs deploy
```

Every update to the pipeline requires repeating these commands.

Files that commonly trigger a redeployment include:

```text
src/ingest/run_ingest.py
src/chunk/run_chunk.py
src/embed/run_embed.py
```

Typical manual deployment commands:

```powershell
docker build ...
docker push ...
gcloud run jobs deploy ...
```

---

# CI/CD with Cloud Build

With Cloud Build, deployments become fully automated.

```text
Git Push
    ↓
Cloud Build Trigger
    ↓
Build Docker Images
    ↓
Push to Artifact Registry
    ↓
Update Cloud Run Jobs
```

No manual deployment steps are required.

---

# Recommended Future Architecture

```text
GitHub
    ↓
Cloud Build Trigger
    ↓
Artifact Registry
    ↓
Cloud Run Jobs
    ↓
Cloud Workflow
    ↓
Cloud Scheduler
```

This architecture enables automatic deployment whenever code is committed to the repository.

---

# Cloud Build Configuration

Create:

```text
cloudbuild.yaml
```

Example configuration for the ingestion job:

```yaml
steps:

- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'build',
      '-f',
      'docker/Dockerfile.ingest',
      '-t',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest',
      '.'
    ]

- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'push',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest'
    ]

- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    [
      'run',
      'jobs',
      'update',
      'undp-ingest-job',
      '--image',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest',
      '--region',
      'northamerica-northeast1'
    ]
```

The same approach can be extended to:

```text
undp-chunk-job
undp-embed-job
```

so that all pipeline jobs are automatically updated after a successful build.

---

# Benefits

Implementing CI/CD provides:

```text
✓ Automated deployments

✓ Reduced manual operations

✓ Faster release cycles

✓ Consistent deployment process

✓ Better production reliability

✓ Improved DevOps practices
```

---

# Current Recommendation

For the current UNDP project, manual deployment is sufficient.

The existing production architecture is:

```text
Cloud Scheduler
    ↓
Cloud Workflow
    ↓
Cloud Run Jobs
    ↓
Google Cloud Storage
    ↓
Streamlit Chatbot
```

CI/CD with Cloud Build is recommended as a future enhancement after the core RAG pipeline and chatbot functionality have been completed and stabilized.

---

# Additional Future Improvements

Potential enhancements after CI/CD:

```text
• Retrieval evaluation framework

• Prompt evaluation framework

• Metadata-based retrieval filters

• Vector database integration
  (Vertex AI Vector Search, Pinecone, Qdrant)

• User authentication

• Monitoring dashboards

• Email or Slack alerts

• Enterprise orchestration with Cloud Composer
```
# step 18: CI/CD
To do :
# Add CI/CD with Cloud Build

## Objective

The UNDP pipeline is currently deployed manually.

Current process:

```text
Code Change
    ↓
docker build
    ↓
docker push
    ↓
gcloud run jobs deploy
```

The goal of this step is to automate deployment using Google Cloud Build.

After implementation:

```text
Git Push
    ↓
Cloud Build Trigger
    ↓
Build Docker Images
    ↓
Push Images to Artifact Registry
    ↓
Update Cloud Run Jobs
    ↓
Pipeline Ready
```

No manual deployment will be required.

---

# Current Architecture

```text
GitHub
      ↓
Manual Build
      ↓
Artifact Registry
      ↓
Cloud Run Jobs
      ↓
Cloud Workflow
      ↓
Cloud Scheduler
```

---

# Target Architecture

```text
GitHub
      ↓
Cloud Build Trigger
      ↓
Cloud Build
      ↓
Artifact Registry
      ↓
Cloud Run Jobs
      ↓
Cloud Workflow
      ↓
Cloud Scheduler
```

---

# Step 1 – Enable Cloud Build API

Enable Cloud Build:

```powershell
gcloud services enable cloudbuild.googleapis.com
```

Verify:

```powershell
gcloud services list --enabled | findstr cloudbuild
```

Expected:

```text
cloudbuild.googleapis.com
```

---

# Step 2 – Create Cloud Build Configuration

Create:

```text
cloudbuild.yaml
```

Project root:

```text
undp_pipeline_prod/
│
├── cloudbuild.yaml
├── docker/
├── src/
├── workflows/
└── ...
```

---

# Step 3 – Configure Ingest Build

Add:

```yaml
steps:

- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'build',
      '-f',
      'docker/Dockerfile.ingest',
      '-t',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest',
      '.'
    ]

- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'push',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest'
    ]

- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    [
      'run',
      'jobs',
      'update',
      'undp-ingest-job',
      '--image',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest',
      '--region',
      'northamerica-northeast1'
    ]
```

---

# Step 4 – Add Chunk Deployment

Add:

```yaml
- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'build',
      '-f',
      'docker/Dockerfile.chunk',
      '-t',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-chunk:latest',
      '.'
    ]

- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'push',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-chunk:latest'
    ]

- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    [
      'run',
      'jobs',
      'update',
      'undp-chunk-job',
      '--image',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-chunk:latest',
      '--region',
      'northamerica-northeast1'
    ]
```

---

# Step 5 – Add Embed Deployment

Add:

```yaml
- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'build',
      '-f',
      'docker/Dockerfile.embed',
      '-t',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-embed:latest',
      '.'
    ]

- name: 'gcr.io/cloud-builders/docker'
  args:
    [
      'push',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-embed:latest'
    ]

- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    [
      'run',
      'jobs',
      'update',
      'undp-embed-job',
      '--image',
      'northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-embed:latest',
      '--region',
      'northamerica-northeast1'
    ]
```

---

# Step 6 – Test Cloud Build Manually

Run:

```powershell
gcloud builds submit
```

Expected:

```text
Build completed successfully
```

Verify:

```text
Artifact Registry updated
Cloud Run Jobs updated
```

---

# Step 7 – Connect GitHub Repository

Navigate:

```text
Cloud Build
    ↓
Triggers
```

Create Trigger:

```text
Name:
undp-main-trigger
```

Repository:

```text
GitHub
```

Branch:

```text
main
```

Configuration:

```text
cloudbuild.yaml
```

---

# Step 8 – Test Automatic Deployment

Make a small change:

```text
README.md
```

Commit:

```powershell
git add .
git commit -m "Test Cloud Build trigger"
git push
```

Expected:

```text
Git Push
    ↓
Cloud Build Trigger
    ↓
Build Success
    ↓
Artifact Registry Updated
    ↓
Cloud Run Jobs Updated
```

---

# Monitoring

View builds:

```text
Cloud Build
    ↓
History
```

View logs:

```text
Cloud Build
    ↓
Build History
    ↓
Build Logs
```

---

# Deliverables

After completing this step:

```text
✓ Cloud Build enabled

✓ cloudbuild.yaml created

✓ GitHub trigger configured

✓ Automatic Docker builds

✓ Automatic Artifact Registry updates

✓ Automatic Cloud Run Job updates

✓ End-to-end CI/CD pipeline
```

---

# Final Production Architecture

```text
GitHub
      ↓
Cloud Build Trigger
      ↓
Cloud Build
      ↓
Artifact Registry
      ↓
Cloud Run Jobs
      ↓
Cloud Workflow
      ↓
Cloud Scheduler
      ↓
Google Cloud Storage
      ↓
Streamlit Chatbot
```

This completes the DevOps automation layer for the UNDP production pipeline.




# Cloud Monitoring Email Notifications for Cloud Run Jobs

## Purpose

Configure Google Cloud Monitoring to send an email whenever a Cloud Run Job execution fails.

This provides operational monitoring for the UNDP RAG pipeline and helps detect failures in:

* `undp-ingest-job`
* `undp-chunk-job`
* `undp-embed-job`

---

# Step 1 — Create an Email Notification Channel

Open:

```text
Google Cloud Console
→ Monitoring
→ Alerting
→ Edit Notification Channels
```

Under **Email**, click:

```text
Add New
```

Enter:

```text
Email Address: mireillewazen@gmail.com
Display Name: UNDP Pipeline Alerts
```

Click:

```text
Save
```

---

# Step 2 — Verify Email Address

Google sends a verification email.

Open the email and click:

```text
Verify Email Address
```

The notification channel must be verified before alerts can be delivered.

---

# Step 3 — Create Alert Policy

Open:

```text
Google Cloud Console
→ Monitoring
→ Alerting
→ Create Policy
```

---

# Step 4 — Select Metric

Click:

```text
Select a Metric
```

Search:

```text
Cloud Run Job
```

Choose:

```text
Cloud Run Job
→ Job
→ Completed exit result and task attempts
```

Click:

```text
Apply
```

---

# Step 5 — Add Failure Filter

Under **Add Filters**, create:

```text
Filter: result
Comparator: !=
Value: succeeded
```

This ensures the alert only evaluates failed executions.

Click:

```text
Done
```

---

# Step 6 — Configure Trigger

Open:

```text
Configure Trigger
```

Set:

```text
Alert Trigger:
Any time series violates
```

```text
Threshold Position:
Above threshold
```

```text
Threshold Value:
0
```

Condition Name:

```text
UNDP Cloud Run Job Failure
```

Click:

```text
Next
```

---

# Step 7 — Configure Notifications

Under **Notification Channels**, select:

```text
UNDP Pipeline Alerts
```

Policy Name:

```text
UNDP Cloud Run Job Failure Alert
```

Optional:

```text
Severity: Critical
```

Click:

```text
Next
```

---

# Step 8 — Review and Create

Review the configuration.

Click:

```text
Create Policy
```

---

# Result

Whenever a Cloud Run Job execution fails, Google Cloud Monitoring will:

1. Create an incident
2. Trigger the alert policy
3. Send an email notification
4. Allow rapid investigation of the failed job

This provides monitoring coverage for the entire UNDP document processing pipeline.

---

# Monitored Jobs

```text
undp-ingest-job
undp-chunk-job
undp-embed-job
```

---

# Example Failure Flow

```text
Cloud Run Job Fails
        ↓
Monitoring Metric Updated
        ↓
Alert Condition Triggered
        ↓
Incident Created
        ↓
Email Sent
        ↓
Investigation Begins
```

---

# Recommended Future Enhancements

* Slack notifications
* Google Chat notifications
* PagerDuty integration
* Cloud Composer DAG failure alerts
* Cloud Workflow execution failure alerts
* Cloud Build deployment failure alerts



## # CI/CD Deployment Overview

## Goal

Automatically deploy the UNDP RAG project whenever code is pushed to GitHub.

---

## Current Process (Manual)

```text
Code Change
    ↓
docker build
    ↓
docker push
    ↓
gcloud run deploy
    ↓
gcloud run jobs deploy
```

---

## Future Process (CI/CD)

```text
Git Push
    ↓
Cloud Build Trigger
    ↓
Build Docker Images
    ↓
Push Images to Artifact Registry
    ↓
Deploy Cloud Run Service
    ↓
Deploy Cloud Run Jobs
```

---

## Components

### Source Control

```text
GitHub Repository
```

### CI/CD Engine

```text
Google Cloud Build
```

### Container Registry

```text
Artifact Registry
```

### Deployment Targets

```text
undp-chatbot
undp-ingest-job
undp-chunk-job
undp-embed-job
```

---

## Required Files

```text
cloudbuild.yaml

docker/
├── Dockerfile.chatbot
├── Dockerfile.ingest
├── Dockerfile.chunk
└── Dockerfile.embed
```

---

## CI/CD Implementation Steps

### Step 1

Create Dockerfiles for all services and jobs.

### Step 2

Create Artifact Registry repository.

### Step 3

Create `cloudbuild.yaml`.

### Step 4

Configure Cloud Build permissions.

### Step 5

Create GitHub → Cloud Build trigger.

### Step 6

Push code to GitHub.

### Step 7

Cloud Build automatically:

* Builds images
* Pushes images to Artifact Registry
* Deploys Cloud Run service
* Deploys Cloud Run Jobs

---

## Final Architecture

```text
GitHub
    ↓
Cloud Build Trigger
    ↓
Cloud Build
    ↓
Artifact Registry
    ↓
Cloud Run Service (Chatbot)
    ↓
Cloud Run Jobs
        ├── undp-ingest-job
        ├── undp-chunk-job
        └── undp-embed-job
```

---

## Benefits

* No manual deployments
* Faster releases
* Consistent deployments
* Production-ready workflow
* Easier maintenance
* Professional cloud architecture

# Configure CI/CD with Cloud Build

## Objective

Automate deployment of the UNDP RAG pipeline and chatbot.

Instead of manually running:

```text
docker build
docker push
gcloud run deploy
gcloud run jobs update
```

Cloud Build will automatically deploy the project whenever code is pushed to GitHub.

---

# Prerequisites Verification

Verify required APIs are enabled:

```powershell
gcloud services list --enabled
```

Required services:

```text
cloudbuild.googleapis.com
artifactregistry.googleapis.com
run.googleapis.com
```

Verified:

```text
Cloud Build API          ✓
Artifact Registry API    ✓
Cloud Run Admin API      ✓
```

---

# Verify Artifact Registry

List repositories:

```powershell
gcloud artifacts repositories list
```

Output:

```text
cloud-run-source-deploy
undp-pipeline
```

Repository used for CI/CD:

```text
undp-pipeline
```

Region:

```text
northamerica-northeast1
```

---

# Verify Dockerfiles

Confirm Dockerfiles exist:

```powershell
dir docker
```

Expected:

```text
Dockerfile.chatbot
Dockerfile.ingest
Dockerfile.chunk
Dockerfile.embed
```

Verified:

```text
Dockerfile.chatbot ✓
Dockerfile.ingest  ✓
Dockerfile.chunk   ✓
Dockerfile.embed   ✓
```

---

# Create Cloud Build Configuration

Create:

```text
cloudbuild.yaml
```

Location:

```text
undp_pipeline_prod/
├── cloudbuild.yaml
├── docker/
├── src/
├── pyproject.toml
└── uv.lock
```

---

# Cloud Build Pipeline

The pipeline performs the following actions:

```text
Build chatbot image
    ↓
Push chatbot image

Build ingest image
    ↓
Push ingest image

Build chunk image
    ↓
Push chunk image

Build embed image
    ↓
Push embed image

Deploy Cloud Run chatbot

Update Cloud Run Jobs:
    • undp-ingest-job
    • undp-chunk-job
    • undp-embed-job
```

---

# Artifact Registry Image Paths

```text
northamerica-northeast1-docker.pkg.dev/$PROJECT_ID/undp-pipeline/undp-chatbot:latest

northamerica-northeast1-docker.pkg.dev/$PROJECT_ID/undp-pipeline/undp-ingest:latest

northamerica-northeast1-docker.pkg.dev/$PROJECT_ID/undp-pipeline/undp-chunk:latest

northamerica-northeast1-docker.pkg.dev/$PROJECT_ID/undp-pipeline/undp-embed:latest
```

---

# Commit Cloud Build Configuration

Check repository status:

```powershell
git status
```

Add configuration file:

```powershell
git add cloudbuild.yaml
```

Create commit:

```powershell
git commit -m "Add Cloud Build CI/CD pipeline"
```

Verify:

```powershell
git status
```

Output:

```text
Your branch is ahead of 'origin/main' by 1 commit
```

This confirms the CI/CD configuration is committed locally.

---

# Push to GitHub

Publish the commit:

```powershell
git push
```

This uploads the Cloud Build configuration to GitHub.

---

# Create Cloud Build Trigger

Open:

```text
Google Cloud Console
→ Cloud Build
→ Triggers
→ Create Trigger
```

Configuration:

```text
Name:
undp-main-trigger

Event:
Push to a branch

Source:
GitHub

Branch:
^main$

Configuration:
Cloud Build configuration file

Path:
cloudbuild.yaml
```

Save the trigger.

---

# Final CI/CD Workflow

```text
Developer pushes code
        ↓
GitHub
        ↓
Cloud Build Trigger
        ↓
cloudbuild.yaml
        ↓
Build Docker Images
        ↓
Push Images to Artifact Registry
        ↓
Deploy Cloud Run Chatbot
        ↓
Update Cloud Run Jobs
```

---

# Daily Deployment Workflow

After CI/CD is configured, deployments become:

```powershell
git add .
git commit -m "New feature"
git push
```

Cloud Build automatically:

```text
Builds images
Pushes images
Deploys chatbot
Updates jobs
```

No manual deployment commands are required.
https://undp-chatbot-1097805338474.northamerica-northeast1.run.app


Configure CI/CD with Cloud Build
Objective

Automate the deployment of the UNDP RAG application using Cloud Build.

Instead of manually running:

docker build
docker push
gcloud run deploy

Cloud Build automatically builds and deploys the application whenever code is pushed to GitHub.

Architecture
GitHub
   ↓
Cloud Build Trigger
   ↓
Build Docker Images
   ↓
Push Images to Artifact Registry
   ↓
Deploy Cloud Run Service
   ↓
Update Cloud Run Jobs
Prerequisites

The following resources must already exist:

Google Cloud Project
Artifact Registry Repository
Cloud Run Service (undp-chatbot)
Cloud Run Jobs
undp-ingest-job
undp-chunk-job
undp-embed-job
GitHub Repository
Create Dockerfiles

Create a dedicated Dockerfile for each pipeline component.

Chatbot
undp_pipeline_prod/docker/Dockerfile.chatbot
Ingest
undp_pipeline_prod/docker/Dockerfile.ingest
Chunk
undp_pipeline_prod/docker/Dockerfile.chunk
Embed
undp_pipeline_prod/docker/Dockerfile.embed
Create Cloud Build Configuration

Create:

undp_pipeline_prod/cloudbuild.yaml

This file defines the CI/CD pipeline.

Cloud Build will:

Build chatbot image
Build ingest image
Build chunk image
Build embed image
Push images to Artifact Registry
Deploy Cloud Run service
Update Cloud Run jobs
Configure Logging

Because a custom service account is used by the trigger, Cloud Build requires explicit logging configuration.

Add:

options:
  logging: CLOUD_LOGGING_ONLY

at the bottom of cloudbuild.yaml.

Connect GitHub Repository

Open:

Cloud Build
→ Repositories
→ Connect Repository

Select:

GitHub

Authenticate and connect:

mireillehaddad/LLMproject
Create Cloud Build Trigger

Open:

Cloud Build
→ Triggers
→ Create Trigger

Configure:

General
Name:
undp-main-trigger

Region:
Global
Event
Push to a branch

Branch:

^main$
Repository
mireillehaddad/LLMproject
Build Configuration
Cloud Build configuration file

Location:

Repository

Path:

/undp_pipeline_prod/cloudbuild.yaml
Service Account

Use:

1097805338474-compute@developer.gserviceaccount.com
Fix Logging Permissions

Grant Cloud Logging permissions:

gcloud projects add-iam-policy-binding undp-project-documents `
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" `
  --role="roles/logging.logWriter"
Test the Pipeline

Make a code change and push to GitHub:

git add .
git commit -m "test cloud build trigger"
git push origin main
Verify Build Execution

Open:

Cloud Build
→ History

A new build should start automatically.

Expected result:

SUCCESS
Successful Deployment Flow

When code is pushed to GitHub:

GitHub
   ↓
Cloud Build Trigger
   ↓
Build Docker Images
   ↓
Push to Artifact Registry
   ↓
Deploy Cloud Run Service
   ↓
Update Cloud Run Jobs
Result

The project now uses automated CI/CD.

Manual deployment commands are no longer required.

Every push to the main branch automatically:

Builds Docker images
Pushes images to Artifact Registry
Deploys the chatbot
Updates ingestion job
Updates chunking job
Updates embedding job

This provides a production-style deployment workflow for the UNDP RAG project.

##  ADD OCR text reading update in chunk the script run_chunk.py



$env:PYTHONPATH="."
uv run streamlit run src/chatbot/app.py

# Add BigQuery Vector Search retreiver
```
 uv add google-cloud-bigquery
```
Create the BigQuery dataset
```
bq mk --location=northamerica-northeast1 undp_rag
```

This script will:

Read embeddings from GCS
Create BigQuery dataset if missing
Create table if missing
Load embeddings into BigQuery

Use this command to create/open the file in VS Code:
```
code src/retrieval/load_embeddings_to_bigquery.py
```
Then write the loader script there.

After that, run:

$env:PYTHONPATH="."
uv run python -m src.retrieval.load_embeddings_to_bigquery

Before running, make sure BigQuery API is enabled:
```
gcloud services enable bigquery.googleapis.com
```
Also make sure your project is set:
```
gcloud config set project undp-project-documents
```


update retriever.py


```
from google import genai
from google.cloud import bigquery
from google.genai.types import EmbedContentConfig

from src.common.settings import settings


TOP_K = 5
DATASET_ID = "undp_rag"
TABLE_ID = "rag_chunks"


def embed_query(client: genai.Client, query: str) -> list[float]:
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=query,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768,
        ),
    )

    return response.embeddings[0].values


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    genai_client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    query_embedding = embed_query(genai_client, question)

    bq_client = bigquery.Client(project=settings.project_id)

    table = f"`{settings.project_id}.{DATASET_ID}.{TABLE_ID}`"

    sql = f"""
    SELECT
        base.id,
        base.text,
        base.source_pdf_blob,
        base.page_number,
        base.year,
        base.country,
        base.project_id,
        base.embedding_blob,
        distance
    FROM VECTOR_SEARCH(
        TABLE {table},
        'embedding',
        (SELECT @query_embedding AS embedding),
        top_k => @top_k,
        distance_type => 'COSINE'
    )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "query_embedding",
                "FLOAT64",
                query_embedding,
            ),
            bigquery.ScalarQueryParameter(
                "top_k",
                "INT64",
                top_k,
            ),
        ]
    )

    rows = bq_client.query(
        sql,
        job_config=job_config,
    ).result()

    results = []

    for row in rows:
        record = dict(row)
        record["score"] = 1 - float(record["distance"])
        results.append(record)

    return results
```

create a Vector Index on your BigQuery table. Without an index, VECTOR_SEARCH performs a brute-force scan of all 8,786 vectors. At your current size it's still workable, but as your dataset grows, the index becomes much more important for latency.

Run this SQL in BigQuery SQL editor:

CREATE VECTOR INDEX rag_chunks_embedding_index
ON `undp-project-documents.undp_rag.rag_chunks`(embedding)
OPTIONS(
  distance_type = 'COSINE',
  index_type = 'IVF'
);

Steps:

Open BigQuery
Click SQL workspace
Paste the SQL above
Click Run

Then check index status:

SELECT
  table_name,
  index_name,
  index_status,
  coverage_percentage
FROM `undp-project-documents.undp_rag.INFORMATION_SCHEMA.VECTOR_INDEXES`
WHERE table_name = 'rag_chunks';

Wait until:

index_status = ACTIVE
coverage_percentage = 100

Important: after creating the index, your existing VECTOR_SEARCH query can stay the same. BigQuery will use the index automatically when possible.

One more thing to improve your retrieval

Once the index reaches 100%, update your VECTOR_SEARCH query to explicitly use approximate nearest neighbor (ANN) search. For example:

VECTOR_SEARCH(
    TABLE `undp-project-documents.undp_rag.rag_chunks`,
    'embedding',
    (SELECT @query_embedding AS embedding),
    top_k => @top_k,
    distance_type => 'COSINE',
    options => '{"use_brute_force": false}'
)

Setting use_brute_force to false tells BigQuery to use the vector index instead of scanning every row.

I got an error when I deployed I need to give access to bq:

gcloud projects add-iam-policy-binding undp-project-documents `
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" `
  --role="roles/bigquery.jobUser"

  also grant read access:
  gcloud projects add-iam-policy-binding undp-project-documents `
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" `
  --role="roles/bigquery.dataViewer"
  


  ############################################

  Run script by script:
  ## Ingest
```
  $env:PYTHONPATH="."
uv run python -m src.ingest.run_ingest
```
## Chunk

```
  $env:PYTHONPATH="."
uv run python -m src.chunk.run_chunk
```
## Embed
```
$env:PYTHONPATH="."
uv run python -m src.embed.run_embed

```
## Load to bq
```
$env:PYTHONPATH="."
uv run python -m src.retrieval.load_embeddings_to_bigquery
```
## Test chatbot locally
```
$env:PYTHONPATH="."
uv run streamlit run src/chatbot/app.py
```

Remark: 
I should add load_embeddings_to_bigquery.py  to the pipeline in docker cloudrun, and ci/cd
##################################################################################################

# Retrieval Evaluation

Two retrieval approaches were implemented and evaluated during the development of the chatbot. The initial implementation performed semantic retrieval using an in-memory Python search, while the final implementation uses BigQuery Vector Search with a BigQuery Vector Index.

## Approach 1: In-Memory Python Retrieval

The first implementation stored document embeddings as JSONL files in Google Cloud Storage. During query execution, all embeddings were loaded into memory, a query embedding was generated using Vertex AI Gemini Embeddings, and cosine similarity was computed in Python using NumPy to retrieve the most relevant document chunks.

### Advantages

* Simple to implement.
* Suitable for small document collections.

### Limitations

* Requires loading all embeddings into application memory.
* Retrieval time increases as the number of document chunks grows.
* Limited scalability for large datasets and production deployments.

---

## Approach 2: BigQuery Vector Search

The final implementation stores document embeddings in BigQuery and performs semantic retrieval using BigQuery Vector Search with a BigQuery Vector Index. For each user query, an embedding is generated using Vertex AI Gemini Embeddings and compared against the indexed embeddings stored in BigQuery. The most relevant document chunks are then returned to the application.

### Advantages

* Scales efficiently to large document collections.
* No need to load embeddings into application memory.
* Faster semantic retrieval through the BigQuery Vector Index.
* Better suited for production and cloud-native deployments.

---

## Final Retrieval Strategy

The project initially relied on an in-memory cosine similarity search implemented in Python. While this approach produced accurate results, it required loading all embeddings into memory and became less efficient as the document collection increased.

The final implementation uses BigQuery Vector Search with a BigQuery Vector Index, allowing semantic retrieval to be performed directly within BigQuery. This architecture improves scalability, reduces memory consumption, and provides faster retrieval for large collections of UNDP project documents. Based on this evaluation, BigQuery Vector Search was selected as the final retrieval strategy.

## Comparison

| Feature           | In-Memory Python Retrieval                   | BigQuery Vector Search               |
| ----------------- | -------------------------------------------- | ------------------------------------ |
| Embedding Storage | JSONL files in Google Cloud Storage          | BigQuery                             |
| Search Method     | NumPy cosine similarity                      | BigQuery `VECTOR_SEARCH`             |
| Vector Index      | No                                           | BigQuery Vector Index                |
| Scalability       | Limited                                      | High                                 |
| Memory Usage      | Loads all embeddings into application memory | Server-side retrieval                |
| Production Ready  | Suitable for small datasets                  | Suitable for large-scale deployments |
| Final Selection   | No                                           | Yes                                  |



#########################################################################################################
# LLM Evaluation

Two prompt templates were evaluated during the development of the chatbot to improve response quality, reduce hallucinations, and ensure that answers remained grounded in the retrieved UNDP project documents.

## Prompt 1: Basic Grounded Prompt

The initial implementation used a concise prompt that instructed the model to answer only using the retrieved document context.

```text
You are a UNDP project assistant.

Answer only using the retrieved document context.

If the answer is not in the context, say:
"I could not find this information in the available UNDP project documents."

Always cite sources using [Source 1], [Source 2], etc.

Do not make up facts.
```

### Advantages

* Simple and easy to maintain.
* Reduced hallucinations compared with an unrestricted prompt.
* Required the model to cite retrieved sources.
* Returned a fallback response when the retrieved context was insufficient.

### Limitations

* Did not explain the structure of the retrieved context.
* Did not instruct the model how to handle conflicting information across multiple documents.
* Did not provide formatting guidance, occasionally resulting in incomplete bullet lists or inconsistent answers.
* Did not explicitly instruct the model to combine information from multiple retrieved document chunks.

---

## Prompt 2: Structured Grounded Prompt

The final implementation uses a more detailed prompt that explains the structure of the retrieved context and provides additional instructions for answer generation.

The improvements include:

* Explaining that each retrieved excerpt contains a source number, document name, page number, and extracted text.
* Restricting the model to use only the retrieved document context.
* Explicitly prohibiting outside knowledge, assumptions, and speculation.
* Preventing the model from inventing facts such as project names, budgets, organizations, beneficiaries, dates, and outcomes.
* Combining information from multiple retrieved document chunks into a single coherent response when appropriate.
* Requiring citations for every factual statement.
* Explaining how to handle conflicting information by citing the corresponding sources.
* Requesting professional, concise, and well-formatted answers.
* Preventing unfinished bullet lists when the available context is incomplete.

### Advantages

* Produces more structured and consistent responses.
* Improves grounding by providing stronger instructions.
* Better handles questions requiring information from multiple retrieved chunks.
* Produces more reliable source citations.
* Reduces incomplete or poorly formatted responses.
* Improves the overall readability of generated answers.

---

## Final Prompt Strategy

The structured grounded prompt was selected as the final implementation because it consistently generated clearer, more reliable, and better-supported answers. Compared with the initial prompt, it improved response formatting, strengthened source attribution, reduced unsupported statements, and handled complex questions involving multiple document excerpts more effectively.

## Comparison

| Feature                                | Initial Prompt | Final Prompt        |
| -------------------------------------- | -------------- | ------------------- |
| Uses retrieved context                 | Yes            | Yes                 |
| Restricts answers to retrieved context | Yes            | Yes                 |
| Prohibits invented facts               | Yes            | Yes (more explicit) |
| Requires source citations              | Yes            | Yes                 |
| Explains retrieved context structure   | No             | Yes                 |
| Combines multiple retrieved sources    | No             | Yes                 |
| Handles conflicting information        | No             | Yes                 |
| Improves response formatting           | Limited        | Yes                 |
| Prevents incomplete bullet lists       | No             | Yes                 |
| Final selection                        | No             | Yes                 |
################################################################################################################

The application is containerized using Docker and deployed on Google Cloud Run. Docker Compose was not used because the architecture relies on managed Google Cloud services (BigQuery, Cloud Storage, Vertex AI, Cloud Run Jobs, Cloud Workflows, and Cloud Scheduler) rather than locally hosted containers. This cloud-native design more closely reflects a production deployment.

################################################################################################################


try this Best Practices
Item	Points
Hybrid search	0/1
Re-ranking	0/1
Query rewriting	0/1???



Step 1. Show feedback buttons

Immediately after displaying the answer, add:

st.markdown("---")
st.subheader("Feedback")

col1, col2 = st.columns(2)

with col1:
    thumbs_up = st.button("👍 Helpful")

with col2:
    thumbs_down = st.button("👎 Not Helpful")

comment = st.text_area(
    "Additional comments (optional)",
    placeholder="Tell us how we can improve..."
)
Step 2. Create a BigQuery table

Create a dataset if you don't already have one.

Example:

Dataset:
undp_feedback

Table:

chatbot_feedback

Schema:

Column	Type
timestamp	TIMESTAMP
question	STRING
answer	STRING
feedback	STRING
comment	STRING

That's all you need.

Step 3. Create a helper function

For example:

from datetime import datetime

from google.cloud import bigquery

from src.common.settings import settings


def save_feedback(question, answer, feedback, comment):

    client = bigquery.Client(project=settings.project_id)

    table = (
        f"{settings.project_id}."
        "undp_feedback.chatbot_feedback"
    )

    rows = [{
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer": answer,
        "feedback": feedback,
        "comment": comment,
    }]

    errors = client.insert_rows_json(table, rows)

    if errors:
        print(errors)
Step 4. Save when the user clicks
if thumbs_up:

    save_feedback(
        question,
        answer,
        "Helpful",
        comment,
    )

    st.success("Thank you for your feedback!")

if thumbs_down:

    save_feedback(
        question,
        answer,
        "Not Helpful",
        comment,
    )

    st.success("Thank you for your feedback!")
Result

The bottom of your chatbot becomes

-----------------------------------

Feedback

👍 Helpful      👎 Not Helpful

Additional comments

___________________________________


When a user clicks a button, a row is inserted into BigQuery.

Later you can build monitoring

Once feedback is stored, you can build a dashboard showing:

Number of questions
Positive vs negative feedback
Most asked countries
Average similarity score
Average response time
I actually recommend one small improvement

Since you already have the retrieved chunks, save a little more information:

Field	Why
timestamp	when
question	what user asked
answer	what Gemini answered
feedback	👍 / 👎
comment	optional
response_time	performance monitoring
country	from top retrieved chunk
project_id	top retrieved project
similarity_score	retrieval quality

This gives you enough data to build a meaningful monitoring dashboard later and demonstrates a production-oriented design.