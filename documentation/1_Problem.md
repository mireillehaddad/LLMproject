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


Top countries found:
Argentina: 29
Bureau Policy & Prog Support: 21
Ukraine: 19
Yemen: 14
Afghanistan: 9
Guatemala: 9
Crisis Bureau: 9
Ethiopia: 8
Pakistan: 8
Syria: 8
Zimbabwe: 7
Lebanon: 7
Sudan, Republic of the: 7
Prog for Palestinian People: 7
Iraq: 6
Turkmenistan: 6
South Sudan, Republic of: 6
Angola: 6
Egypt: 6
Honduras: 6
Democratic Republic of Congo: 5
India: 5
Mozambique: 5
Colombia: 5
Cuba: 4
Burundi: 4
Turkiye: 4
Chad: 4
Brazil: 4
Dominica: 3
Uruguay: 3
Nigeria: 3
Indonesia: 3
Paraguay: 3
Morocco: 3
Bangladesh: 3
Moldova, Republic of: 2
Serbia: 2
Haiti: 2
Bureau for Dev. Policy: 2
Cyprus: 2
Nepal: 2
Central African Republic: 2
Panama: 2
Congo: 2
Albania: 1
Dakar Regional Service Centre: 1
Fiji: 1
Libya: 1
Burkina Faso: 1


Ingested pdf's for
 Iraq
Lebanon
Prog for Palestinian People
Yemen


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


