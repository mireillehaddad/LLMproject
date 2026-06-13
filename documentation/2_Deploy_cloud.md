# Deploying the UNDP RAG Chatbot to Google Cloud Run

## Overview

The UNDP RAG Chatbot was deployed as a Streamlit application on Google Cloud Run. The deployment process uses Cloud Build to build a Docker container and Cloud Run to host the application.

The application uses:

* Google Cloud Run
* Cloud Build
* Artifact Registry
* Vertex AI Gemini
* Google Cloud Storage
* Streamlit
* uv package manager

---

# 1. Prerequisites

Project structure:

```text
undp_pipeline/
├── app.py
├── app_gemini.py
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── .dockerignore
└── README.md
```

---

# 2. Authenticate with Google Cloud

Login to Google Cloud:

```bash
gcloud auth login
```

Authenticate Application Default Credentials:

```bash
gcloud auth application-default login
```

---

# 3. Configure the GCP Project

Set the active project:

```bash
gcloud config set project undp-project-documents
```

Verify:

```bash
gcloud config get-value project
```

Expected output:

```text
undp-project-documents
```

---

# 4. Enable Required Services

Enable Cloud Run:

```bash
gcloud services enable run.googleapis.com
```

Enable Cloud Build:

```bash
gcloud services enable cloudbuild.googleapis.com
```

Enable Artifact Registry:

```bash
gcloud services enable artifactregistry.googleapis.com
```

Enable Vertex AI:

```bash
gcloud services enable aiplatform.googleapis.com
```

---

# 5. Create the Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8080"]
```

---

# 6. Create .dockerignore

```text
.venv
__pycache__
.env
data
*.pdf
.git
```

---

# 7. Grant Required IAM Permissions


Grant Cloud Build permissions:

```bash
gcloud projects add-iam-policy-binding undp-project-documents \
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"
```

Grant Vertex AI permissions:

```bash
gcloud projects add-iam-policy-binding undp-project-documents \
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

These permissions allow:

* Cloud Build to build the container image
* Cloud Run to access Gemini Embedding and Gemini models through Vertex AI

---

# 8. Deploy the Application

Deploy directly from source:

```bash
gcloud run deploy undp-chatbot \
  --source . \
  --region northamerica-northeast1 \
  --allow-unauthenticated
```

Cloud Run automatically:

1. Uploads source code
2. Builds the Docker image using Cloud Build
3. Stores the image in Artifact Registry
4. Creates a Cloud Run revision
5. Routes traffic to the latest revision

---

# 9. Successful Deployment

Deployment completed successfully:

```text
Service: undp-chatbot
Revision: undp-chatbot-00001-qpx
Traffic: 100%
```

Public URL:

```text
https://undp-chatbot-1097805338474.northamerica-northeast1.run.app
```

---

# 10. Test the Application

Open the Cloud Run URL:

```text
https://undp-chatbot-1097805338474.northamerica-northeast1.run.app
```

Verify that:

* The Streamlit interface loads
* Questions can be submitted
* Gemini embeddings are generated successfully
* Relevant document chunks are retrieved
* Gemini generates answers using retrieved context

---



# Deployment Architecture

```text
Local Source Code
        │
        ▼
Cloud Build
        │
        ▼
Artifact Registry
        │
        ▼
Cloud Run
        │
        ▼
Vertex AI Gemini
        │
        ▼
Public Streamlit Application
```


check the AI chatbot at

 https://undp-chatbot-1097805338474.northamerica-northeast1.run.app/