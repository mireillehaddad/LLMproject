Use local embeddings first. It is simpler and no API cost.

Install:
```
uv pip install sentence-transformers --link-mode=copy
```
Create embed_undp_chunks.py:

Run:
```
python embed_undp_chunks.py
```

Later, switching from:

SentenceTransformer("all-MiniLM-L6-v2")

to:

gemini-embedding-001

is a relatively small change because the rest of the pipeline stays the same:

chunks.jsonl
    ↓
create embedding
    ↓
store embedding
    ↓
vector search

Only the embedding generation code changes.

What I would do
Run the current embedding script with sentence-transformers.
Verify that the embeddings/ folder is created.
Build a simple vector search script.
Build a simple RAG chatbot.
Then migrate embeddings to Vertex AI.

This way you'll have a working prototype quickly.

One thing I'd change

Instead of saving the full embedding vectors back to GCS long-term, save them temporarily for learning/testing. Once you move to Vertex AI + a vector database, you'll likely store:

chunk text
metadata
embedding vector

in a vector store rather than huge JSONL files.

So for now:

python embed_undp_chunks.py

is the right next step. If it works, the next file we'll write is:

search_undp_documents.py

complete ingestion pipeline:

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

The next step is retrieval.

Create:

search_undp_documents.py

The flow will be:

User question
    ↓
Create embedding for question
    ↓
Load document embeddings
    ↓
Cosine similarity
    ↓
Return Top 5 chunks

For example:

Question:
"What projects are related to health in Lebanon?"

The script returns:

1. Chunk 234 (score 0.87)
2. Chunk 121 (score 0.84)
3. Chunk 95  (score 0.81)
...

Before adding Gemini, test retrieval quality first.