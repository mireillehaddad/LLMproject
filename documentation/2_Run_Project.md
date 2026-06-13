## How to Run the Project

### 1. Clone the repository

```bash
git clone https://github.com/mireillehaddad/LLMproject.git
cd undp_pipeline
```

### 2. Create and activate the virtual environment

```bash
uv venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If using `uv.lock`:

```bash
uv sync
```

<!-- If dependencies need to be installed manually:

```bash
uv pip install requests google-cloud-storage python-dotenv pypdf numpy streamlit google-genai --link-mode=copy
``` -->

### 4. Configure Google Cloud

```bash
gcloud config set project undp-project-documents
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
```

### 5. Run the ingestion pipeline

```bash
python ingest_undp_pdfs.py
```

### 6. Chunk the PDFs

```bash
python chunk_undp_pdfs.py
```

### 7. Generate Gemini embeddings

```bash
python embed_undp_chunks_gemini.py
```

### 8. Test retrieval

```bash
python search_undp_documents.py
```

### 9. Run the command-line RAG chatbot

```bash
python rag_undp_chatbot.py
```

### 10. Run the Streamlit web app

```bash
streamlit run app_gemini.py
```

Then open:

```text
http://localhost:8501
```