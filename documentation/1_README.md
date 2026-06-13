# LLMproject


## Problem

UNDP publishes project documents in PDF format on the Open UNDP website:

https://open.undp.org/

Finding specific information across hundreds of pages of project documents is difficult and time-consuming.

---

## Solution

This project builds a Retrieval-Augmented Generation (RAG) chatbot that allows users to ask questions about UNDP project documents (Knowledge base of the bot) and receive accurate answers grounded in the source documents.

The system automatically:

1. Ingests UNDP project documents using the Open UNDP API.
2. Downloads and processes PDF documents.
3. Splits documents into chunks.
4. Creates vector embeddings for semantic search.
5. Retrieves the most relevant document chunks for a user query.
6. Uses Gemini to generate answers based on the retrieved context.
7. Provides a web interface built with Streamlit and deployed on Google Cloud Run.

---

## Data Source

Open UNDP API:

https://api.open.undp.org/api_documentation/api#!/default/individual_project_data

---

## Architecture

```text
Open UNDP API
       │
       ▼
PDF Documents
       │
       ▼
Document Processing
       │
       ▼
Chunking
       │
       ▼
Embeddings Generation
       │
       ▼
Vector Search
       │
       ▼
Relevant Context Retrieval
       │
       ▼
Gemini
       │
       ▼
Streamlit Web Application
```

---

## Web Application

The chatbot is available at:

https://undp-chatbot-1097805338474.northamerica-northeast1.run.app/

---

## Features

* Automatic ingestion of UNDP project documents
* PDF processing and chunking
* Semantic search using embeddings
* Retrieval-Augmented Generation (RAG)
* Gemini-powered question answering
* Streamlit user interface
* Deployment on Google Cloud Run

---

## Example Questions

* What projects are currently active in Lebanon?
* Which UNDP projects focus on climate change?
* What is the budget of a specific project?
* What outcomes are expected from a project?
* Which stakeholders are involved in a project?

```
```



## 1. Create the Project Folder

```bash
mkdir undp_pipeline
cd undp_pipeline
```

---

## 2. Create a Virtual Environment

```bash
uv venv
```

Activate:

```bash
.venv\Scripts\Activate.ps1
```

---

## 3. Configure GCP Project

```bash
gcloud config set project undp-project-documents
```

Verify:

```bash
gcloud config get-value project
```

Expected:

```text
undp-project-documents
```

---

## 4. Authenticate with GCP

```bash
gcloud auth application-default login
```

---

## 5. Install Dependencies

```bash
uv pip install requests google-cloud-storage python-dotenv pypdf numpy streamlit google-genai --link-mode=copy
```

---

## 6. Create Google Cloud Storage Bucket

Bucket:

```text
undp-project-documents-llm-2026
```

Folder structure:

```text
raw/
processed/
embeddings/
metadata/
```

---

## 7. Test GCS Access

Create:

```text
test_upload.py
```

Run:

```bash
python test_upload.py
```

Verify:

```bash
gcloud storage ls gs://undp-project-documents-llm-2026
```

---

# Data Ingestion Pipeline

## 8. Download UNDP Project Documents

Create:

```text
ingest_undp_pdfs.py
```

Run:

```bash
python ingest_undp_pdfs.py
```

Downloads PDFs from the UNDP Open Data API and stores them in:

```text
raw/year=YYYY/country=COUNTRY/project_id=PROJECT_ID/
```

---

## 9. Chunk Documents

Create:

```text
chunk_undp_pdfs.py
```

Run:

```bash
python chunk_undp_pdfs.py
```

Reads PDFs from:

```text
raw/
```

Creates chunk files in:

```text
processed/
```

---

## 10. Enable Vertex AI

```bash
gcloud services enable aiplatform.googleapis.com
```

---

## 11. Generate Gemini Embeddings

Create:

```text
embed_undp_chunks_gemini.py
```

Run:

```bash
python embed_undp_chunks_gemini.py
```

Uses:

```text
gemini-embedding-001
```

Stores embeddings in:

```text
embeddings/
```

---

# Retrieval Testing

## 12. Test Retrieval

Create:

```text
search_undp_documents.py
```

Run:

```bash
python search_undp_documents.py
```

Example question:

```text
What digital initiatives are mentioned in the projects?
```

---

# RAG Chatbot

## 13. Create RAG Chatbot

Create:

```text
rag_undp_chatbot.py
```

Run:

```bash
python rag_undp_chatbot.py
```

Workflow:

```text
Question
↓
Retrieve Relevant Chunks
↓
Gemini 2.5 Flash
↓
Answer with Sources
```

---

# Streamlit Web Application

## 14. Create Streamlit App

Create:

```text
app.py
```

Run:

```bash
streamlit run app.py
```

Features:

- Question answering over UNDP project documents
- Gemini-powered responses
- Source citations
- Retrieval scores
- Interactive web interface

---

# Architecture

```text
UNDP API
    ↓
PDF Ingestion
    ↓
Google Cloud Storage (raw)
    ↓
Chunking
    ↓
Google Cloud Storage (processed)
    ↓
Gemini Embeddings
    ↓
Google Cloud Storage (embeddings)
    ↓
Similarity Search
    ↓
Gemini 2.5 Flash
    ↓
Streamlit Web Application
```