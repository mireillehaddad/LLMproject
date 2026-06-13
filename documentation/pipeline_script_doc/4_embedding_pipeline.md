# Embeddings and Retrieval

## Use Local Embeddings First

For the first prototype, use local embeddings with `sentence-transformers`.

This is simpler because:

* It is easy to run locally.
* It does not require an API call.
* It avoids API cost during testing.
* It allows the RAG pipeline to be tested quickly.

---

## Install Sentence Transformers

```bash
uv pip install sentence-transformers --link-mode=copy
```

---

## Create the Embedding Script

Create the following file:

```text
embed_undp_chunks.py
```

This script will read the processed document chunks, create embeddings, and save them for retrieval.

---

## Run the Embedding Script

```bash
python embed_undp_chunks.py
```

After running the script, verify that the following folder is created:

```text
embeddings/
```

---

## Why Start with Local Embeddings?

The first version can use:

```python
SentenceTransformer("all-MiniLM-L6-v2")
```

Later, the project can be migrated to Gemini embeddings:

```text
gemini-embedding-001
```

This migration is a relatively small change because the rest of the RAG pipeline stays the same.

```text
chunks.jsonl
    ↓
create embedding
    ↓
store embedding
    ↓
vector search
```

Only the embedding generation code changes.

---

## Recommended Development Order

1. Run the current embedding script with `sentence-transformers`.
2. Verify that the `embeddings/` folder is created.
3. Build a simple vector search script.
4. Build a simple RAG chatbot.
5. Migrate embeddings to Vertex AI later.

This approach gives a working prototype quickly before adding cloud-based embedding services.

---

## Temporary Storage Note

For learning and testing, it is acceptable to save full embedding vectors in JSONL files or in Google Cloud Storage.

However, for a production version, embeddings should usually be stored in a vector store together with:

```text
chunk text
metadata
embedding vector
```

Instead of keeping large JSONL embedding files long-term, a vector database or managed vector search service should be used.

---

## Current Pipeline

The ingestion pipeline is:

```text
UNDP API
    ↓
Download PDFs
    ↓
Store in GCS (raw/)
    ↓
Extract text
    ↓
Chunk documents
    ↓
Generate embeddings
    ↓
Store embeddings in GCS
```

The next step is retrieval.

---

