# RAG Chatbot

The retrieval pipeline has been successfully implemented and tested.

The search process:

* Loads document embeddings from Google Cloud Storage (GCS)
* Embeds the user question using the same embedding model used during indexing
* Computes cosine similarity between the question embedding and document embeddings
* Returns the most relevant chunks

A deduplication step was added to avoid returning identical chunks originating from the same project, file, and page.

The retrieved results produced similarity scores in the range of approximately **0.40–0.45**, which is acceptable for this prototype. The final answer quality will be improved by Gemini, which will use the retrieved chunks as context to generate a grounded response.

## Next Step: Full RAG Chatbot

Create the script:

```text
rag_undp_chatbot.py
```

The chatbot workflow is:

1. Accept a user question
2. Retrieve the most relevant document chunks
3. Send the question and retrieved context to Gemini
4. Generate a final answer
5. Display supporting sources

## Environment Setup

### Enable Vertex AI

Enable the Vertex AI API once for the project:

```bash
gcloud services enable aiplatform.googleapis.com
```

### Install Gemini SDK

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

## Running the Chatbot

Execute:

```bash
python rag_undp_chatbot.py
```

Example question:

```text
What are the objectives of the Lebanon Host Communities Support Project?
```

The chatbot will:

* Retrieve the most relevant chunks from the UNDP project documents
* Send the context to Gemini through Vertex AI
* Generate a grounded answer
* Display the source documents and pages used to support the answer
