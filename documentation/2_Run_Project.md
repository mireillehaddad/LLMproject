# How to Run the Project

## 1. Clone the Repository

```bash
git clone https://github.com/mireillehaddad/LLMproject.git
cd undp_pipeline
```

---

## 2. Create and Activate the Virtual Environment

```bash
uv venv
```

Activate:

```bash
.venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

Install all dependencies from the lock file:

```bash
uv sync
```

---

## 4. Configure Google Cloud

Set the active project:

```bash
gcloud config set project undp-project-documents
```

Authenticate Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```

Enable Vertex AI:

```bash
gcloud services enable aiplatform.googleapis.com
```

Verify the active project:

```bash
gcloud config get-value project
```

Expected output:

```text
undp-project-documents
```

---

## 5. Google Cloud Storage

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

### Folder Description

| Folder      | Purpose                                     |
| ----------- | ------------------------------------------- |
| raw/        | Original PDF documents downloaded from UNDP |
| processed/  | Chunked document files                      |
| embeddings/ | Gemini embedding vectors                    |
| metadata/   | Metadata files generated during ingestion   |

---

## 6. Run the Ingestion Pipeline

Download project documents from the UNDP Open Data API:

```bash
python ingest_undp_pdfs.py
```

Documents are stored in:

```text
raw/year=YYYY/country=COUNTRY/project_id=PROJECT_ID/
```

---

## 7. Chunk the PDFs

Generate document chunks:

```bash
python chunk_undp_pdfs.py
```

Reads:

```text
raw/
```

Writes:

```text
processed/
```

---

## 8. Generate Gemini Embeddings

Create vector embeddings for all document chunks:

```bash
python embed_undp_chunks_gemini.py
```

Embedding model:

```text
gemini-embedding-001
```

Embeddings are stored in:

```text
embeddings/
```

---

## 9. Test Retrieval

Run semantic search against the document embeddings:

```bash
python search_undp_documents.py
```

Example question:

```text
What digital initiatives are mentioned in the projects?
```

The retrieval pipeline:

```text
Question
    ↓
Create Question Embedding
    ↓
Load Document Embeddings
    ↓
Cosine Similarity Search
    ↓
Return Top Matching Chunks
```

---

## 10. Run the Command-Line RAG Chatbot

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

## 11. Run the Streamlit Web Application

Start the web interface:

```bash
streamlit run app_gemini.py
```

Then open:

```text
http://localhost:8501
```

Features:

* Question answering over UNDP project documents
* Gemini-powered responses
* Source citations
* Retrieval scores
* Interactive web interface

---

# Project Architecture

```text
UNDP Open Data API
        ↓
Download PDFs
        ↓
Google Cloud Storage (raw/)
        ↓
PDF Text Extraction
        ↓
Document Chunking
        ↓
Google Cloud Storage (processed/)
        ↓
Gemini Embeddings
        ↓
Google Cloud Storage (embeddings/)
        ↓
Similarity Search
        ↓
Gemini 2.5 Flash
        ↓
Streamlit Web Application
```

---

# Data Flow

```text
User Question
        ↓
Question Embedding
        ↓
Similarity Search
        ↓
Top Matching Chunks
        ↓
Gemini 2.5 Flash
        ↓
Grounded Answer + Sources
```
