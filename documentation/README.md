# LLMproject


Problem:
UNDP publishes project documents in PDF format on the website https://open.undp.org/.
Finding information across hundreds of pages is difficult.


This project builds a RAG chatbot that automatically ingests UNDP documents from API (https://api.open.undp.org/api_documentation/api#!/default/individual_project_data),creates embeddings, retrieves relevant content, and answers questions using Gemini.




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