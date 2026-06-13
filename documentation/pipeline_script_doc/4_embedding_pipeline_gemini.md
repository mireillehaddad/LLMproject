# Migrating from Sentence Transformers to Gemini Embeddings

## 1. Keep Existing Documents and Chunks

Do **not** rerun document ingestion or chunking.

Keep the existing folders:

```text
raw/
processed/
```

---

## 2. Delete Existing Sentence Transformer Embeddings

Remove the previously generated embeddings from Google Cloud Storage:

```bash
gcloud storage rm --recursive gs://undp-project-documents-llm-2026/embeddings/**
```

---

## 3. Install the Gemini SDK

Install the Google GenAI SDK:

```bash
uv pip install google-genai --link-mode=copy
```

---

## 4. Enable Vertex AI

Enable the Vertex AI API:

```bash
gcloud services enable aiplatform.googleapis.com
```

---

## 5. Authenticate with Google Cloud

Authenticate and configure the project:

```bash
gcloud auth application-default login

gcloud config set project undp-project-documents
```

---

## 6. Create a Gemini Embedding Pipeline

Create a new script:

```text
embed_undp_chunks_gemini.py
```

The script will:

* Read chunked documents from:

```text
processed/*.jsonl
```

* Generate embeddings using:

```text
gemini-embedding-001
```

* Save the embeddings for retrieval.

---

## 7. Update the Streamlit Application

The application should no longer use Sentence Transformers:

```python
from sentence_transformers import SentenceTransformer
```

Instead, use Gemini for:

* Document embeddings
* Question embeddings
* Answer generation

---

## 8. Generate Gemini Embeddings

Run the embedding pipeline:

```bash
python embed_undp_chunks_gemini.py
```

This will create a new embedding index based on Gemini embeddings.

---

## 9. Start the Application

Launch the Streamlit chatbot:

```bash
streamlit run app.py
```

---

## Important

Document embeddings and query embeddings **must be generated using the same embedding model**.

If document embeddings are created with:

```text
gemini-embedding-001
```

then user questions must also be embedded with:

```text
gemini-embedding-001
```

Mixing embedding models (for example, Sentence Transformers for documents and Gemini for questions) will significantly reduce retrieval quality and should be avoided.
