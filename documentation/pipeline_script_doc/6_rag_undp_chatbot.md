# RAG Chatbot

## Retrieval Validation

The retrieval pipeline has been successfully implemented and tested.

The search process performs the following steps:

1. Loads document embeddings from Google Cloud Storage (GCS)
2. Embeds the user question using the same embedding model used during indexing
3. Computes cosine similarity between the question embedding and document embeddings
4. Returns the most relevant document chunks

To improve retrieval quality, a deduplication step was added to prevent returning identical chunks originating from the same project, file, and page.

The retrieved results produced cosine similarity scores in the range of approximately **0.40–0.45**, which is acceptable for this prototype. The final answer quality will be enhanced by Gemini, which will use the retrieved chunks as context to generate grounded responses.

---

## Next Step: Full RAG Chatbot

Create the following script:

```text
rag_undp_chatbot.py
```

The chatbot workflow is:

```text
User Question
      ↓
Retrieve Relevant Chunks
      ↓
Send Context + Question to Gemini
      ↓
Generate Final Answer
      ↓
Display Sources
```

### Chatbot Features

* Accept a user question
* Retrieve the most relevant document chunks
* Send the question and retrieved context to Gemini
* Generate a grounded answer
* Display supporting sources

---

## Environment Setup

### Enable Vertex AI

Enable the Vertex AI API for the project:

```bash
gcloud services enable aiplatform.googleapis.com
```

### Install the Gemini SDK

```bash
uv pip install google-genai --link-mode=copy
```

### Configure Authentication

Authenticate using Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```

### Configure the GCP Project

Set the active project:

```bash
gcloud config set project undp-project-documents
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

## Running the Chatbot

Execute:

```bash
python rag_undp_chatbot.py
```

Example question:

```text
What are the objectives of the Lebanon Host Communities Support Project?
```

---

## Expected Behavior

The chatbot will:

1. Retrieve the most relevant chunks from the UNDP project documents
2. Send the retrieved context and user question to Gemini through Vertex AI
3. Generate a grounded answer based on the retrieved evidence
4. Display the source documents and page numbers used to support the answer

---

## Complete RAG Architecture

```text
UNDP API
    ↓
Download PDFs
    ↓
Store in GCS (raw/)
    ↓
Extract Text
    ↓
Chunk Documents
    ↓
Generate Embeddings
    ↓
Store Embeddings in GCS
    ↓
User Question
    ↓
Retrieve Top Chunks
    ↓
Gemini (Vertex AI)
    ↓
Grounded Answer + Sources
```
