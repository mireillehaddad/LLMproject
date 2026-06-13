
This script will search your embeddings.

2. The retrieval flow
Question
↓
Embed the question
↓
Load embeddings from GCS
↓
Compare question embedding with chunk embeddings
↓
Return top matching chunks
3. Install needed package

You already have sentence-transformers, but also install:

uv pip install numpy --link-mode=copy
4. Build search script

The script will read from:

gs://undp-project-documents-llm-2026/embeddings/

and return top results with:

score
text
country
year
project_id
page_number
source_gcs_path
5. Test with questions

Examples:

What is the Lebanon Host Communities Support Project?
What are the project objectives in Lebanon?
What partners are mentioned in the project document?
6. After retrieval works

Add Gemini:

top chunks + question → Gemini → final answer with sources

# Create 
search_undp_documents.py


Flow:

question
↓
top chunks
↓
Gemini writes final answer
↓
show sources

Before Gemini, improve retrieval by removing duplicate chunks using:

dedupe_key = (
    row.get("project_id"),
    row.get("file_name"),
    row.get("page_number"),
    row.get("text")[:200],
)

