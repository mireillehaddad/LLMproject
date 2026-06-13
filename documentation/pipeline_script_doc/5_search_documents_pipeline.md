# Retrieval and Semantic Search

## Create the Search Script

Create the following file:

```text
search_undp_documents.py
```

This script will perform semantic search over the document embeddings and return the most relevant chunks for a user question.

---

## Retrieval Flow

The retrieval process follows these steps:

```text
Question
    ↓
Embed the question
    ↓
Load embeddings from GCS
    ↓
Compare question embedding with chunk embeddings
    ↓
Return top matching chunks
```

---

## Install Required Packages

If not already installed, install NumPy:

```bash
uv pip install numpy --link-mode=copy
```

The project should already have `sentence-transformers` installed from the previous step.

---

## Search Data Source

The search script will read embeddings stored in:

```text
gs://undp-project-documents-llm-2026/embeddings/
```

For each retrieved chunk, the script should return:

* Similarity score
* Chunk text
* Country
* Year
* Project ID
* Page number
* Source GCS path

Example output:

```text
Score: 0.87
Country: Lebanon
Year: 2026
Project ID: 01003798
Page Number: 15
Source: gs://...
Text: ...
```

---

## Test Retrieval

After implementing the search script, test retrieval quality using questions such as:

```text
What is the Lebanon Host Communities Support Project?

What are the project objectives in Lebanon?

What partners are mentioned in the project document?
```

Verify that the returned chunks are relevant before introducing an LLM.

---

## Add Gemini for Answer Generation

Once retrieval is working correctly, add Gemini to generate final answers.

The workflow becomes:

```text
Question
    ↓
Retrieve top chunks
    ↓
Send question + retrieved chunks to Gemini
    ↓
Generate final answer
    ↓
Display sources
```

---

## Complete RAG Flow

```text
Question
    ↓
Top matching chunks
    ↓
Gemini generates final answer
    ↓
Show answer with sources
```

---

## Improving Retrieval Quality

Before integrating Gemini, improve retrieval quality by removing duplicate chunks.

A simple deduplication key can be created using:

```python
dedupe_key = (
    row.get("project_id"),
    row.get("file_name"),
    row.get("page_number"),
    row.get("text")[:200],
)
```

This helps avoid returning multiple nearly identical chunks from the same document page.

---

## Development Goal

The retrieval component should be validated independently before adding answer generation.

A good retrieval system should consistently return relevant chunks for a variety of project-related questions. Once retrieval quality is satisfactory, Gemini can be added to generate grounded answers using the retrieved context.
