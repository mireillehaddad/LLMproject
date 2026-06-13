# LLMproject


## Problem

UNDP publishes project documents in PDF format on the Open UNDP website:

https://open.undp.org/

Finding specific information across hundreds of pages of project documents is difficult and time-consuming.

---

## Solution

This project builds a Retrieval-Augmented Generation (RAG) chatbot that allows users to ask questions about UNDP project documents (Knowledge base of the bot) and receive accurate answers grounded in the source documents.

The system automatically:

1. Ingests UNDP project documents using the Open UNDP API.
2. Downloads and processes PDF documents.
3. Splits documents into chunks.
4. Creates vector embeddings for semantic search.
5. Retrieves the most relevant document chunks for a user query.
6. Uses Gemini to generate answers based on the retrieved context.
7. Provides a web interface built with Streamlit and deployed on Google Cloud Run.

---

## Data Source

Open UNDP API:

https://api.open.undp.org/api_documentation/api#!/default/individual_project_data

---

## Architecture

```text
Open UNDP API
       │
       ▼
PDF Documents
       │
       ▼
Document Processing
       │
       ▼
Chunking
       │
       ▼
Embeddings Generation
       │
       ▼
Vector Search
       │
       ▼
Relevant Context Retrieval
       │
       ▼
Gemini
       │
       ▼
Streamlit Web Application
```

---

## Web Application

The chatbot is available at:

https://undp-chatbot-1097805338474.northamerica-northeast1.run.app/

---

## Features

* Automatic ingestion of UNDP project documents
* PDF processing and chunking
* Semantic search using embeddings
* Retrieval-Augmented Generation (RAG)
* Gemini-powered question answering
* Streamlit user interface
* Deployment on Google Cloud Run

---

## Example Questions

* What projects are currently active in Lebanon?
* Which UNDP projects focus on climate change?
* What is the budget of a specific project?
* What outcomes are expected from a project?
* Which stakeholders are involved in a project?

```
```
