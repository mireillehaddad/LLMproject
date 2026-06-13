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
